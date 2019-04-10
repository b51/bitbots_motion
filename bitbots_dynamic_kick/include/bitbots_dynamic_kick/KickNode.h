#ifndef BITBOTS_DYNAMIC_KICK_KICK_NODE_H
#define BITBOTS_DYNAMIC_KICK_KICK_NODE_H

#include <string>
#include <ros/ros.h>
#include <dynamic_reconfigure/server.h>
#include <actionlib/server/simple_action_server.h>
#include <bitbots_msgs/KickAction.h>
#include <bitbots_dynamic_kick/DynamicKickConfig.h>
#include "bitbots_dynamic_kick/KickEngine.h"

typedef actionlib::SimpleActionServer<bitbots_msgs::KickAction> ActionServer;

class KickNode {
public:
    KickNode();
    void reconfigure_callback(bitbots_dynamic_kick::DynamicKickConfig &config, uint32_t level);
    void execute(const bitbots_msgs::KickGoalConstPtr& goal);
private:
    ros::NodeHandle m_node_handle;
    ActionServer m_server;
    KickEngine m_engine;
    int m_engine_rate;

    /**
     * Do main loop in which engine.tick() get called repeatedly.
     *
     * The ActionServer is taken into account meaning that a cancelled goal should no longer get processed.
     */
    void loop_engine();
};

#endif  // BITBOTS_DYNAMIC_KICK_KICK_NODE_H
