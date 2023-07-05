# -*- coding: utf-8 -*-
"""
Created on Mon Jan 30 14:12:43 2023

@author: yangh
"""

import jpype as jp
import jpype.imports as jimport
import os
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import time
import gzip
import shutil
from datetime import date
from shapely import geometry

def runMatsim(configFile):
    """Path for MATSim executable"""
    jimport.registerDomain('org')
    classpath = os.pathsep.join(('matsim-14.0-release/matsim-14.0/matsim-14.0.jar', 'matsim-14.0-release/matsim-14.0/libs/'))
    """Path for DVRPT executable"""
    classpath2 = os.pathsep.join(('DVRPT/out/artifacts/DVRPT_slow_jar/DVRPT.jar','DVRPT/nyu-implementation/src/main/java'))
    try:
        jp.startJVM("C:\\Program Files\\Java\\jdk-11.0.16\\bin\\server\\jvm.dll",'-ea', classpath=[classpath, classpath2])
    except:
        pass

    from org.matsim.core.scenario import ScenarioUtils
    from org.matsim.core.config import ConfigUtils
    from org.matsim.api.core.v01 import Id
    from org.matsim.core.controler import Controler
    from org.matsim.core.controler.OutputDirectoryHierarchy import OverwriteFileSetting

    config = ConfigUtils.loadConfig(configFile)
    config.controler().setOverwriteFileSetting(OverwriteFileSetting.deleteDirectoryIfExists)

    scenario = ScenarioUtils.loadScenario(config)

    controler = Controler(scenario)

    controler.run()
    print("=== END OF MATSIM SIMULATION ===")
    
    """Read output_legs.csv from MATSim to fetch 'drt' request for Rideshare simulation"""
    
def runDVRPT(drt_fleet):  
    nodes = pd.read_csv('DVRPT/nyc_sub_nodes_update.csv')
    poly = geometry.Polygon([[nodes.x[i], nodes.y[i]] for i in nodes.index])
    
    with gzip.open('output/example_tele/BUILT.output_legs.csv.gz', 'rb') as f_in:
        with open('output/example_tele/BUILT.output_legs.csv', 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
            
    matsim_legs = pd.read_csv('output/example_tele/BUILT.output_legs.csv', sep = ';')
    """Create request log"""
    matsim_legs_drt = matsim_legs[matsim_legs['mode'] == drt_fleet]
    i_region = []
    for i in range(0, matsim_legs_drt.shape[0]):
      x1 = matsim_legs_drt.iloc[i,:].start_x
      y1 = matsim_legs_drt.iloc[i,:].start_y
      x2 = matsim_legs_drt.iloc[i,:].end_x
      y2 = matsim_legs_drt.iloc[i,:].end_y
      if (poly.distance(geometry.Point(float(x1),float(y1))) <= 1500) & (poly.distance(geometry.Point(float(x2),float(y2))) <= 1500):
        i_region.append(i)
    
    matsim_legs_in_region = matsim_legs_drt.iloc[i_region,:]
    # matsim_legs_in_region = matsim_legs_in_region[matsim_legs_in_region['mode'] == drt_fleet]
    matsim_legs_in_region = matsim_legs_in_region[matsim_legs_in_region['dep_time'] <= '24:00:00']
    matsim_legs_in_region['request_time'] = str(date.today()) + 'T' + matsim_legs_in_region['dep_time'] + 'Z'
    rideshare_request = matsim_legs_in_region[['start_x', 'start_y', 'end_x', 'end_y','request_time']]
    rideshare_request.to_csv('requests_nyu_SF.csv', index = False)
    matsim_legs_in_region.to_csv('all_drt_legs.csv')
    
    if drt_fleet == 'drt_1':
        jp.JClass("edu.nyu.intramodal.Main").main([])
        print("=== END OF DVRPT Fast ===")
    else:
        jp.JClass("edu.nyu.intramodal.Main").main([])
        print("=== END OF DVRPT Slow ===")
    
    
    # matsim_legs_drt = matsim_legs[matsim_legs['mode'] == drt_fleet]
    request_info = pd.read_csv('requests_info.csv')
    request_info['trip_id'] = matsim_legs_in_region.reset_index()['trip_id']
    matsim_legs_drt_service = matsim_legs_drt.merge(request_info, how = 'left', on = 'trip_id')
    matsim_legs_drt_service['status'] = matsim_legs_drt_service['status'].fillna('rejected')
    matsim_legs_drt_service = matsim_legs_drt_service.fillna(0)
    matsim_legs_drt_service['tr_time'] = matsim_legs_drt_service['dropoff_t'] - matsim_legs_drt_service['submission_t']
    matsim_legs_drt_service['w_p_time'] = ((matsim_legs_drt_service['origin_x'] - matsim_legs_drt_service['pickup_x'])**2 + (matsim_legs_drt_service['origin_y'] - matsim_legs_drt_service['pickup_y'])**2)**0.5*1.4/2.733
    matsim_legs_drt_service['w_d_time'] = ((matsim_legs_drt_service['dest_x'] - matsim_legs_drt_service['dropoff_x'])**2 + (matsim_legs_drt_service['dest_y'] - matsim_legs_drt_service['dropoff_y'])**2)**0.5*1.4/2.733
    matsim_legs_drt_service['total_time'] = matsim_legs_drt_service['w_p_time'] + matsim_legs_drt_service['w_d_time'] + matsim_legs_drt_service['tr_time']
    matsim_legs_drt_service['total_time'] = [0 if j < 0 else j for j in matsim_legs_drt_service['total_time']]
    matsim_legs_drt_service['t_time'] = matsim_legs_drt_service.apply(lambda x: time.strftime("%H:%M:%S", time.gmtime(x['total_time'])),axis=1)
    matsim_legs_drt_service['distance'] = ((matsim_legs_drt_service['origin_x'] - matsim_legs_drt_service['dest_x'])**2 + (matsim_legs_drt_service['origin_y'] - matsim_legs_drt_service['dest_y'])**2)**0.5
    matsim_drt_served = matsim_legs_drt_service[matsim_legs_drt_service.status != 'rejected']
    average_speed = matsim_drt_served.distance.sum()*1.4/matsim_drt_served.total_time.sum()
    num_drt_passenger = matsim_drt_served.shape[0]
    matsim_legs_drt_service.to_csv('drt_updated.csv')
    
    with gzip.open('output/example_tele/BUILT.output_plans.xml.gz', 'rb') as f_in:
      with open('output/example_tele/BUILT.output_plans.xml', 'wb') as f_out:
          shutil.copyfileobj(f_in, f_out)
    
    return matsim_legs_drt_service,  average_speed, num_drt_passenger

def MatsimInput(matsim_legs_drt_service, InputFile, drt_fleet):
    tree = ET.parse(InputFile)
    root = tree.getroot()
    
    passengers = np.unique(np.array(matsim_legs_drt_service.person.astype(str)))
    
    """Update plan file to reflect the drt service time in DVRPT"""
    for i in root.findall('person'):
      if i.attrib['id'] in passengers:
        print(i.attrib)
        for j in i.findall('plan'):
          print(j.attrib)
          r_pass = matsim_legs_drt_service[matsim_legs_drt_service.person == int(i.attrib['id'])]
          if j.attrib['selected'] == 'yes':
            ii = 0
            iii = 0
            j.attrib.pop('score', None)
            for x in j.findall('leg'):
                if x.attrib['mode'] == drt_fleet[0]:
                  r_pass_1 = r_pass[r_pass['mode'] == drt_fleet[0]]
                  if ii <= r_pass_1.shape[0]-1:
                    if (r_pass_1.iloc[ii,:].status != 'rejected') | (r_pass_1.iloc[ii,:].tr_time > 0):
                        x.attrib['trav_time'] = r_pass_1.iloc[ii,:].t_time
                        for y in x.findall('route'):
                            y.attrib['trav_time'] = r_pass_1.iloc[ii,:].t_time
                    else:                    
                        x.attrib['mode'] = 'pt'
                        x.attrib.pop('trav_time', None)
                        x.remove(x.find('attributes'))
                        x.remove(x.find('route'))
                    ii = ii + 1
                  else:
                    x.attrib['mode'] = 'pt'
                    x.attrib.pop('trav_time', None)
                    x.remove(x.find('attributes'))
                    x.remove(x.find('route'))
                elif x.attrib['mode'] == drt_fleet[1]:
                  r_pass_2 = r_pass[r_pass['mode'] == drt_fleet[1]]
                  if iii <= r_pass_2.shape[0]-1:
                    if (r_pass_2.iloc[iii,:].status != 'rejected') | (r_pass_2.iloc[iii,:].tr_time > 0):
                        x.attrib['trav_time'] = r_pass_2.iloc[iii,:].t_time
                        for y in x.findall('route'):
                            y.attrib['trav_time'] = r_pass_2.iloc[iii,:].t_time
                    else:                    
                        x.attrib['mode'] = 'pt'
                        x.attrib.pop('trav_time', None)
                        x.remove(x.find('attributes'))
                        x.remove(x.find('route'))
                    iii = iii + 1
                  else:
                    x.attrib['mode'] = 'pt'
                    x.attrib.pop('trav_time', None)
                    x.remove(x.find('attributes'))
                    x.remove(x.find('route'))
          else:
             i.remove(j)
      else:
          j_pre = i.find('plan')
          score_pre = j_pre.attrib['score']
          n = 0
          for j in i.findall('plan'):
            score = j.attrib['score']
            j.attrib['selected'] = 'yes'
            if score < score_pre:
                i.remove(j)
            elif score >= score_pre:
                if n > 0:
                  i.remove(j_pre)
                  j_pre = j
                  score_pre = score
            n = n + 1

    with open('matsim-14.0-release/nyc_drt.xml', 'wb') as f:
            f.write('<?xml version="1.0" encoding="UTF-8" ?>\n<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n'.encode('utf8'))
            tree.write(f, 'utf-8')
    
    del tree
    del root
    
def config_mod(config_file_next, average_speed_1, average_speed_2, random):
    tree = ET.parse(config_file_next)
    root = tree.getroot()
    mode = 'none'
    
    for i in root.findall('module'):
      if i.attrib['name'] == 'planscalcroute':
        for j in i.iter('parameterset'):
          if j.attrib['type'] == 'teleportedModeParameters':
            for x in j.findall('param'):
              if (x.attrib['name'] == 'mode') & (x.attrib['value'] == 'drt_1'):
                mode = 'drt_1'
              elif (x.attrib['name'] == 'mode') & (x.attrib['value'] == 'drt_2'):
                mode = 'drt_2'
              if (x.attrib['name'] == 'teleportedModeSpeed'):
                if mode == 'drt_1':
                  x.attrib['value'] = str(average_speed_1)
                elif mode == 'drt_2':
                  x.attrib['value'] = str(average_speed_2)
      elif i.attrib['name'] == 'global':
        for j in i.iter('param'):
          if j.attrib['name'] == 'randomSeed':
            # j.attrib['value'] = str(4711)
            if random == True:
                j.attrib['value'] = str(np.random.randint(5000))
      elif i.attrib['name'] == 'controler':
        for j in i.iter('param'):
          if j.attrib['name'] == 'lastIteration':
            j.attrib['value'] = '5'

    with open(config_file_next, 'wb') as f:
        f.write('<?xml version="1.0" encoding="UTF-8" ?>\n<!DOCTYPE config SYSTEM "./dtd/config_v2.dtd">\n'.encode('utf8'))
        tree.write(f, 'utf-8')
    
    del tree
    del root


configFile = 'matsim-14.0-release/config-with-mode-vehicles-drt-tele_2_income.xml'
configFile_1 = 'matsim-14.0-release/config-with-mode-vehicles-drt-tele_2_income_updated.xml'
runMatsim(configFile)
[matsim_legs_drt_service_1, drt_speed_1, drt_passenger_1] = runDVRPT('drt_1')
[matsim_legs_drt_service_2, drt_speed_2, drt_passenger_2] = runDVRPT('drt_2')
matsim_legs_drt_service = pd.concat([matsim_legs_drt_service_1, matsim_legs_drt_service_2], axis = 0)
MatsimInput(matsim_legs_drt_service, 'output/example_tele/BUILT.output_plans.xml', ['drt_1','drt_2'])
drt_1_v = []
drt_1_p = []
# drt_speed_1 = 7
drt_1_v.append(drt_speed_1)
drt_1_p.append(drt_passenger_1)
drt_2_v = []
drt_2_p = []
# drt_speed_2 = 7
drt_2_v.append(drt_speed_2)
drt_2_p.append(drt_passenger_2)
ph_record = pd.read_csv('output/example_tele/BUILT.ph_modestats.txt', sep = '\t')

NoSD = 60

for n in range(1, NoSD):
    config_mod(configFile_1, drt_speed_1, drt_speed_2, True)
    runMatsim(configFile_1)
    [matsim_legs_drt_service_1, drt_speed_1, drt_passenger_1] = runDVRPT('drt_1')
    [matsim_legs_drt_service_2, drt_speed_2, drt_passenger_2] = runDVRPT('drt_2')
    matsim_legs_drt_service = pd.concat([matsim_legs_drt_service_1, matsim_legs_drt_service_2], axis = 0)
    MatsimInput(matsim_legs_drt_service, 'output/example_tele/BUILT.output_plans.xml', ['drt_1','drt_2'])
    drt_1_v.append(drt_speed_1)
    drt_1_p.append(drt_passenger_1)
    drt_2_v.append(drt_speed_2)
    drt_2_p.append(drt_passenger_2)
    a = pd.read_csv('output/example_tele/BUILT.ph_modestats.txt', sep = '\t')
    a['day'] = n
    ph_record = pd.concat([ph_record,a], axis = 0)
    
    if n >= 39:

        config_mod(configFile_1, drt_speed_1, drt_speed_2, False)
        tree = ET.parse(configFile_1)
        root = tree.getroot()
        
        for i in root.findall('module'):
          if i.attrib['name'] == 'controler':
            for j in i.iter('param'):
              if j.attrib['name'] == 'lastIteration':
                j.attrib['value'] = '0'
          if i.attrib['name'] == 'strategy':
            for j in i.iter('param'):
              if j.attrib['name'] == 'fractionOfIterationsToDisableInnovation':
                j.attrib['value'] = '0.0'
                  
        with open(configFile_1, 'wb') as f:
            f.write('<?xml version="1.0" encoding="UTF-8" ?>\n<!DOCTYPE config SYSTEM "./dtd/config_v2.dtd">\n'.encode('utf8'))
            tree.write(f, 'utf-8')
        
        runMatsim(configFile_1)
        
        with gzip.open('output/example_tele/BUILT.output_plans.xml.gz', 'rb') as f_in:
          with open('output/example_tele/BUILT.output_plans.xml', 'wb') as f_out:
              shutil.copyfileobj(f_in, f_out)
        # [matsim_legs_drt_service_1, drt_speed_1, drt_passenger_1] = runDVRPT('drt_1')
        # [matsim_legs_drt_service_2, drt_speed_2, drt_passenger_2] = runDVRPT('drt_2')
        # matsim_legs_drt_service = pd.concat([matsim_legs_drt_service_1, matsim_legs_drt_service_2], axis = 0)
        # MatsimInput(matsim_legs_drt_service, 'output/example_tele/BUILT.output_plans.xml', ['drt_1','drt_2'])
        # drt_1_v.append(drt_speed_1)
        # drt_1_p.append(drt_passenger_1)
        # drt_2_v.append(drt_speed_2)
        # drt_2_p.append(drt_passenger_2)
        # a = pd.read_csv('output/example_tele/BUILT.ph_modestats.txt', sep = '\t')
        # a['day'] = n
        # ph_record = pd.concat([ph_record,a], axis = 0)
        
        tree = ET.parse(configFile_1)
        root = tree.getroot()
        
        for i in root.findall('module'):
          if i.attrib['name'] == 'strategy':
            for j in i.iter('param'):
              if j.attrib['name'] == 'fractionOfIterationsToDisableInnovation':
                j.attrib['value'] = '0.8'
                  
        with open(configFile_1, 'wb') as f:
            f.write('<?xml version="1.0" encoding="UTF-8" ?>\n<!DOCTYPE config SYSTEM "./dtd/config_v2.dtd">\n'.encode('utf8'))
            tree.write(f, 'utf-8')
        
        
        plan_name = 'fast_onefifth.lowVOT_flat7_' + str(n) + '.xml'
        
        os.rename("output/example_tele/BUILT.output_plans.xml", plan_name)


drt_v_table_1 = pd.DataFrame(drt_1_v)
drt_p_table_1 = pd.DataFrame(drt_1_p)
drt_v_table_2 = pd.DataFrame(drt_2_v)
drt_p_table_2 = pd.DataFrame(drt_2_p)
drt_stat = pd.concat([drt_v_table_1, drt_p_table_1, drt_v_table_2, drt_p_table_2], axis = 1)    
ph_names = 'ph_record_nyc_fast_equity_onefifth_lowVOT_flat7' + '.csv'
drt_names = 'drt_stat_nyc_fast_equity_onefifth_lowVOT_flat7' + '.csv'
ph_record.to_csv(ph_names, index = False)
drt_stat.to_csv(drt_names, index = False)



