import rospy 
from dynamic_stack_decider.abstract_decision_element import AbstractDecisionElement
from dynamic_stack_decider.sequence_element import SequenceElement
import humanoid_league_msgs.msg
from bitbots_hcm.hcm_dsd.hcm_blackboard import STATE_ANIMATION_RUNNING, STATE_CONTROLABLE, STATE_FALLEN, STATE_FALLING, STATE_HARDWARE_PROBLEM, STATE_MOTOR_OFF, STATE_PENALTY, STATE_PICKED_UP, STATE_RECORD, STATE_SHUT_DOWN, STATE_STARTUP, STATE_WALKING, STATE_HCM_OFF
from bitbots_hcm.hcm_dsd.actions.wait_for import WaitForIMU, WaitForMotors
from bitbots_hcm.hcm_dsd.actions.stay import StayShutDown, StayAnimationRunning, StayControlable, StayInPenalty, StayMotorsOff, StayPickedUp, StayRecord, StayWalking
from bitbots_hcm.hcm_dsd.actions.play_animation import PlayAnimationStandUp, PlayAnimationFalling, PlayAnimationPenalty, PlayAnimationMotorOff, PlayAnimationSitDown, PlayAnimationWalkready
from bitbots_hcm.hcm_dsd.actions.change_motor_power import TurnMotorsOff, TurnMotorsOn
from bitbots_hcm.hcm_dsd.actions.stop_walking import StopWalking

class StartHcm(AbstractDecisionElement):
    """
    Initializes HCM. 
    """
    def perform(self, blackboard, reevaluate=False):
        if blackboard.shut_down_request:
            blackboard.current_state = STATE_SHUT_DOWN
            return self.push_action_sequence(SequenceElement, [PlayAnimationSitDown, StayShutDown], [None, None])  
        else:
            if not reevaluate:
                blackboard.current_state = STATE_STARTUP
            if blackboard.simulation_active:
                return self.push(Penalty)      
            else:                
                return self.push(CheckIMU)
    def get_reevaluate(self):
        return True


class CheckIMU(AbstractDecisionElement):
    """
    Checks if we are getting information from the IMU.
    Since the HCM can not detect falls without it, we will shut everything down if we dont have an imu.
    """

    def perform(self, blackboard, reevaluate=False):
        if  blackboard.last_imu_update_time.to_sec == 0:
            # wait for the IMU to start
            blackboard.current_state = STATE_STARTUP
            return self.push(WaitForIMU)
        elif blackboard.is_imu_timeout():
            # tell that we have a hardware problem
            blackboard.current_state = STATE_HARDWARE_PROBLEM
            # wait for IMU
            return self.push(WaitForIMU)
        return self.push(Penalty)

    def get_reevaluate(self):
        return True


class Penalty(AbstractDecisionElement):
    """
    Initializes HCM
    """

    def perform(self, blackboard, reevaluate=False):
        if blackboard.penalized:
            # we do an action sequence to go into penalty and to stay there      
            return self.push_action_sequence(SequenceElement, [StopWalking, PlayAnimationPenalty, StayInPenalty], [None, None, None])  
        else:
            return self.push(MotorOffTimer)

    def get_reevaluate(self):
        return True


class MotorOffTimer(AbstractDecisionElement):
    """
    Decides on switching servo power
    """

    def perform(self, blackboard, reevaluate=False):
        if blackboard.simulation_active:
            return self.push(Fallen)
        # check if the time is reached
        if blackboard.is_motor_off_time():
            rospy.logwarn_throttle(5, "Didn't recieve goals for " + str(blackboard.motor_off_time) + " seconds. Will shut down the motors and wait for commands.")
            blackboard.current_state = STATE_MOTOR_OFF
            # we do an action sequence to turn off the motors and stay in motor off  
            return self.push_action_sequence(SequenceElement, [PlayAnimationSitDown, TurnMotorsOff, StayMotorsOff], [None, None, None])   
        elif not blackboard.are_motors_on():
            # we have to turn the motors on
            return self.push(TurnMotorsOn)
        else:
            # motors are on and we can continue
            return self.push(CheckMotors)

    def get_reevaluate(self):
        return True


class CheckMotors(AbstractDecisionElement):
    """
    Checks if we are getting information from the motors.
    Since the HCM is not able to work without motor connection, we will stop if there are no values.
    """

    def perform(self, blackboard, reevaluate=False):
        if not blackboard.are_motors_available():
            # tell that we have a hardware problem                            
            blackboard.current_state = STATE_HARDWARE_PROBLEM
            # wait for motors to connect
            return self.push(WaitForMotors)
        return self.push(Record)

    def get_reevaluate(self):
        return True


class Record(AbstractDecisionElement):
    """
    Decides if the robot is currently recording animations
    """

    def perform(self, blackboard, reevaluate=False):
        # check if the robot is currently recording animations
        if blackboard.record_active:
            blackboard.current_state = STATE_RECORD
            return self.push(StayRecord)
        else:
            # robot is not recording
            return self.push(PickedUp)

    def get_reevaluate(self):
        return True


class PickedUp(AbstractDecisionElement):
    """
    Decides if the robot is currently picked up
    """

    def perform(self, blackboard, reevaluate=False):
        # check if the robot is currently beeing picked up
        if blackboard.is_robot_picked_up():
            blackboard.current_state = STATE_PICKED_UP
            # we do an action sequence to tgo to walkready and stay in picked up state            
            return self.push_action_sequence(SequenceElement, [PlayAnimationWalkready, StayPickedUp], [None, None])
        else:
            # robot is not picked up
            return self.push(Fallen)

    def get_reevaluate(self):
        return True


class Fallen(AbstractDecisionElement):
    """
    Decides if the robot is currently fallen and lying on the ground
    """

    def perform(self, blackboard, reevaluate=False):
        # check if the robot is currently laying on the ground
        if blackboard.is_stand_up_active and blackboard.is_fallen():
            blackboard.current_state = STATE_FALLEN
            # we play a stand up animation            
            rospy.loginfo("FALLEN")
            return self.push(PlayAnimationStandUp)
        else:
            # robot is not fallen
            return self.push(Falling)

    def get_reevaluate(self):
        return True

class Falling(AbstractDecisionElement):
    """
    Decides if the robot is currently falling and has to act on this
    """

    def perform(self, blackboard, reevaluate=False):
        # check if the robot is currently falling
        if blackboard.falling_detection_active and blackboard.is_falling():
            blackboard.current_state = STATE_FALLING
            # we play a falling animation            
            return self.push(PlayAnimationFalling)
        else:
            # robot is not fallen
            return self.push(BehaviorAnimation)

    def get_reevaluate(self):
        return True


class BehaviorAnimation(AbstractDecisionElement):
    """
    Decides if the robot is currently wants to play an animation comming from the behavior
    """

    def perform(self, blackboard, reevaluate=False):
        if blackboard.external_animation_running:
            blackboard.current_state = STATE_ANIMATION_RUNNING
            return self.push(StayAnimationRunning)
        else:
            return self.push(Walking)

    def get_reevaluate(self):
        return True


class Walking(AbstractDecisionElement):
    """
    Decides if the robot is currently walking
    """

    def perform(self, blackboard, reevaluate=False):
        if blackboard.is_currently_walking():
            blackboard.current_state = STATE_WALKING
            if blackboard.animation_requested:
                blackboard.animation_requested = False
                # we are walking but we have to stop to play an animation
                return self.push(StopWalking)
            else:                
                # we are walking and can stay like this
                return self.push(StayWalking)
        else:
            return self.push(Controlable)

    def get_reevaluate(self):
        return True


class Controlable(AbstractDecisionElement):
    """
    Decides if the robot is currently controlable
    """

    def perform(self, blackboard, reevaluate=False):
        # check if the robot is in a walkready pose
        if not blackboard.is_walkready():
            blackboard.current_state = STATE_ANIMATION_RUNNING
            self.push(PlayAnimationWalkready)
        else:
            blackboard.current_state = STATE_CONTROLABLE
            return self.push(StayControlable)

    def get_reevaluate(self):
        return True