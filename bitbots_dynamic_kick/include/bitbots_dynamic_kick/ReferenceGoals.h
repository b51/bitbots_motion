#ifndef BITBOTS_DYNAMIC_KICK_REFERENCEGOALS_H
#define BITBOTS_DYNAMIC_KICK_REFERENCEGOALS_H

#include <bio_ik/goal.h>
#include <ros/ros.h>

class ReferenceLinkGoalBase : public bio_ik::Goal {
private:
    std::string link_name_;
    std::string reference_link_name_;
public:
    ReferenceLinkGoalBase()
            : link_name_("")
            , reference_link_name_("")
            , Goal() {}
    ReferenceLinkGoalBase(const std::string& link_name, const std::string& reference_link_name, double weight = 1.0)
            : link_name_(link_name)
            , reference_link_name_(reference_link_name) {
        weight_ = weight;
    }
    void setLinkName(const std::string& name) { link_name_ = name; }
    void setReferenceLinkName(const std::string& name) { reference_link_name_ = name; }
    void describe(bio_ik::GoalContext& context) const final {
        Goal::describe(context);
        context.addLink(link_name_);
        context.addLink(reference_link_name_);
    }
    inline const bio_ik::Frame& getLinkFrame(const bio_ik::GoalContext& context) const { return context.getLinkFrame(0); }
    inline const bio_ik::Frame& getReferenceLinkFrame(const bio_ik::GoalContext& context) const { return context.getLinkFrame(1); }
};

class ReferenceOrientationGoal : public ReferenceLinkGoalBase {
    tf::Quaternion orientation_;

public:
    ReferenceOrientationGoal()
            : orientation_(0, 0, 0, 1)
            , ReferenceLinkGoalBase() {}
    ReferenceOrientationGoal(const std::string& link_name, const std::string& reference_link_name,
                             const tf::Quaternion& orientation, double weight = 1.0)
            : ReferenceLinkGoalBase(link_name, reference_link_name, weight)
            , orientation_(orientation.normalized()) {}
    inline void setOrientation(const tf::Quaternion& orientation) { orientation_ = orientation.normalized(); }
    double evaluate(const bio_ik::GoalContext& context) const override {
        bio_ik::Frame reference_to_goal = bio_ik::inverse(getReferenceLinkFrame(context) * getLinkFrame(context));
        return fmin((orientation_ - reference_to_goal.getOrientation()).length2(), (orientation_ + reference_to_goal.getOrientation()).length2());
    }
};

class ReferencePoseGoal : public ReferenceLinkGoalBase {
    bio_ik::Frame frame_;  // Goal pose relative to reference link

public:
    ReferencePoseGoal() : ReferenceLinkGoalBase() {}
    ReferencePoseGoal(const std::string &link_name, const std::string &reference_link_name,
                      const tf::Vector3 &position, const tf::Quaternion &orientation,
                      double weight = 1.0)
            : ReferenceLinkGoalBase(link_name, reference_link_name, weight)
            , frame_(position, orientation) {}
    inline void setPosition(tf::Vector3 position) { frame_.setPosition(position); }
    inline void setOrientation(tf::Quaternion rotation) { frame_.setOrientation(rotation); }
    double evaluate(const bio_ik::GoalContext& context) const override {
        double e = 0.0;

        bio_ik::Frame reference_to_goal = bio_ik::inverse(getReferenceLinkFrame(context)) * getLinkFrame(context);

        e += reference_to_goal.getPosition().distance2(frame_.getPosition());
        e += fmin((frame_.getOrientation() - reference_to_goal.getOrientation()).length2(), (frame_.getOrientation() + reference_to_goal.getOrientation()).length2());

        return e;
    }
};

class ReferenceHeightGoal : public ReferenceLinkGoalBase {
    double height_;

public:
    ReferenceHeightGoal() : ReferenceLinkGoalBase() {}
    ReferenceHeightGoal(const std::string &link_name, const std::string &reference_link_name,
                        double height, double weight = 1.0)
            : ReferenceLinkGoalBase(link_name, reference_link_name, weight)
            , height_(height) {}
    inline void setHeight(double height) { height_ = height; }
    double evaluate(const bio_ik::GoalContext& context) const override {
        bio_ik::Frame reference_to_goal = bio_ik::inverse(getReferenceLinkFrame(context)) * getLinkFrame(context);
        double height = reference_to_goal.getPosition().z();
        double e = abs(height - height_);
        return e;
    }
};

class ReferenceMinPlanarDistance : public ReferenceLinkGoalBase {
    double distance_;

public:
    ReferenceMinPlanarDistance() : ReferenceLinkGoalBase() {}
    inline void setDistance(double distance) { distance_ = distance; }
    double evaluate(const bio_ik::GoalContext& context) const override {
        bio_ik::Frame reference_to_goal = bio_ik::inverse(getReferenceLinkFrame(context)) * getLinkFrame(context);

        double distance = sqrt(pow(reference_to_goal.pos.x(), 2) + pow(reference_to_goal.pos.y(), 2));
        double e = fmax(0.0, distance_ - distance);
        return e * e;
    }
};

#endif //BITBOTS_DYNAMIC_KICK_REFERENCEGOALS_H
