#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist
from turtle_interfaces.msg import TurtleArray
from turtle_interfaces.srv import CatchTurtle
from functools import partial
import math

class TurtleController(Node):
    def __init__(self):
        super().__init__("turtle_controller")
        self.declare_parameter("frequency", 100.0)
        self.declare_parameter("catch_closest_turtle_first", True)

        self.frequency_ = self.get_parameter("frequency").value
        self.catch_closest_turtle_first_ = self.get_parameter(
            "catch_closest_turtle_first").value
        self.pose_ = None
        self.turtle_to_catch_ = None

        self.cmd_publisher_ = self.create_publisher(
            Twist,
            "turtle1/cmd_vel",
            10
        )
        self.pose_subscriber_ = self.create_subscription(
            Pose,
            "turtle1/pose",
            self.poseCallback,
            10
        )
        self.alive_turtles_subscriber_ = self.create_subscription(
            TurtleArray,
            "alive_turtles",
            self.aliveTurtles,
            10
        )
        self.timer_ = self.create_timer(1.0 / self.frequency_, self.controlLoop)

    def poseCallback(self, msg):
        self.pose_ = msg

    def aliveTurtles(self, msg):
        if self.pose_ is None:
            return

        if len(msg.turtles) > 0:
            if self.catch_closest_turtle_first_:
                closest_turtle = None
                closest_turtle_distance = None

                for turtle in msg.turtles:
                    dist_x = turtle.x - self.pose_.x
                    dist_y = turtle.y - self.pose_.y
                    distance = math.sqrt(dist_x * dist_x + dist_y * dist_y)

                    if closest_turtle is None or distance < closest_turtle_distance:
                        closest_turtle = turtle
                        closest_turtle_distance = distance

                self.turtle_to_catch_ = closest_turtle
            else:
                self.turtle_to_catch_ = msg.turtles[0]

    def controlLoop(self):
        if self.pose_ is None or self.turtle_to_catch_ is None:
            return

        dist_x = self.turtle_to_catch_.x - self.pose_.x
        dist_y = self.turtle_to_catch_.y - self.pose_.y

        distance = math.sqrt(dist_x * dist_x + dist_y * dist_y)

        msg = Twist()

        if distance > 0.5:
            msg.linear.x = 2 * distance

            goal_theta = math.atan2(dist_y, dist_x)
            diff = goal_theta - self.pose_.theta

            if diff > math.pi:
                diff -= 2 * math.pi
            elif diff < -math.pi:
                diff += 2 * math.pi

            msg.angular.z = 6 * diff
        else:
            msg.linear.x = 0.0
            msg.angular.z = 0.0
            self.catchCall(self.turtle_to_catch_.name)
            self.turtle_to_catch_ = None

        self.cmd_publisher_.publish(msg)

    def catchCall(self, turtle_name):
        self.client_ = self.create_client(CatchTurtle, "catch_turtle")

        while not self.client_.wait_for_service(1.0):
            self.get_logger().warn("Service not available, waiting again...")

        self.request_ = CatchTurtle.Request()
        self.request_.name = turtle_name

        self.future_ = self.client_.call_async(self.request_)
        self.future_.add_done_callback(
            partial(
                self.responseCatchCallback,
                turtle_name=turtle_name
            )
        )

    def responseCatchCallback(self, future, turtle_name):
        try:
            response = future.result()

            if not response.success:
                self.get_logger().error(
                    "Turtle " + str(turtle_name) + " could not be caught"
                )

        except Exception as e:
            self.get_logger().error(
                "Service call failed %r" % (e,)
            )


def main(args=None):
    rclpy.init(args=args)
    turtle_controller = TurtleController()
    rclpy.spin(turtle_controller)
    turtle_controller.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
