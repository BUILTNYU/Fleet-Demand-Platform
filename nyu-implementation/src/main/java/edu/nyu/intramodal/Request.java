package edu.nyu.intramodal;

import java.util.ArrayList;
import java.util.List;

public class Request {

    int origin, dest, submission_t, p_latest_arr_t;
    Double origin_x, origin_y, dest_x, dest_y;
    Integer pickup_t, dropoff_t, assigned_veh;
    boolean transfer;
    String status;

    Request(int origin, int dest, int submission_t, int p_latest_arr_t, Integer pickup_t, Integer dropoff_t,
            String status, List<Integer> assigned_vehs, boolean transfer, double origin_x, double origin_y, double dest_x, double dest_y){
        this.origin = origin;
        this.dest = dest;
        this. submission_t = submission_t;
        this.p_latest_arr_t = p_latest_arr_t;
        this.pickup_t = pickup_t;
        this.dropoff_t = dropoff_t;
        this.status = status;
        this.assigned_veh = assigned_veh;
        this.transfer = transfer;
        this.origin_x = origin_x;
        this.origin_y = origin_y;
        this.dest_x = dest_x;
        this.dest_y = dest_y;
    }
}
