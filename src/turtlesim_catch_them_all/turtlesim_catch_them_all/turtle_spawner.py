#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from turtlesim.srv import Spawn
from turtlesim.srv import Kill
from turtle_interfaces.msg import Turtle
from turtle_interfaces.msg import TurtleArray
from turtle_interfaces.srv import CatchTurtle
from functools import partial
import math
import random

class TurtleSpawner(Node):
    def __init__(self):
        super().__init__("turtle_spawner")
        self.declare_parameter("prefix", "turtle")
        self.declare_parameter("counter", 0)
        self.declare_parameter("frequency", 1.0)

        self.turtle_name_prefix_ = self.get_parameter("prefix").value
        self.turtle_counter_ = self.get_parameter("counter").value
        self.frequency_ = self.get_parameter("frequency").value
        self.alive_turtles_ = []

        self.alive_turtles_publisher_ = self.create_publisher(
            TurtleArray,
            "alive_turtles",
            10
        )
        self.catch_turtle_service_ = self.create_service(
            CatchTurtle,
            "catch_turtle",
            self.catchTurtles
        )
        self.timer = self.create_timer(
            1.0 / self.frequency_,
            self.spawnTurtle
        )

    def catchTurtles(self, request, response):
        for turtle in self.alive_turtles_:
            if turtle.name == request.name:
                self.killCall(request.name)
                response.success = True
                return response

        response.success = False
        return response

    def aliveTurtles(self):
        msg = TurtleArray()
        msg.turtles = self.alive_turtles_
        self.alive_turtles_publisher_.publish(msg)

    def spawnTurtle(self):
        self.turtle_counter_ += 1
        name = self.turtle_name_prefix_ + str(self.turtle_counter_)
        x = random.uniform(0.0, 11.0)
        y = random.uniform(0.0, 11.0)
        theta = random.uniform(0.0, 2 * math.pi)
        self.spawnCall(x, y, theta, name)

    def spawnCall(self, x, y, theta, turtle_name):
        self.client_ = self.create_client(Spawn, "spawn")

        while not self.client_.wait_for_service(1.0):
            self.get_logger().warn("Service not available, waiting again...")

        self.request_ = Spawn.Request()
        self.request_.x = x
        self.request_.y = y
        self.request_.theta = theta
        self.request_.name = turtle_name

        self.future_ = self.client_.call_async(self.request_)
        self.future_.add_done_callback(
            partial(
                self.responseSpawnCallback,
                x=x,
                y=y,
                theta=theta,
                turtle_name=turtle_name
            )
        )

    def responseSpawnCallback(self, future, x, y, theta, turtle_name):
        try:
            response = future.result()

            if response.name != "":
                self.get_logger().info(
                    "Turtle " + response.name + " is now alive"
                )

                new_turtle = Turtle()
                new_turtle.x = x
                new_turtle.y = y
                new_turtle.theta = theta
                new_turtle.name = response.name

                self.alive_turtles_.append(new_turtle)
                self.aliveTurtles()

        except Exception as e:
            self.get_logger().error(
                "Service call failed %r" % (e,)
            )

    def killCall(self, turtle_name):
        self.client_ = self.create_client(Kill, "kill")

        while not self.client_.wait_for_service(1.0):
            self.get_logger().warn("Service not available, waiting again...")

        self.request_ = Kill.Request()
        self.request_.name = turtle_name

        self.future_ = self.client_.call_async(self.request_)
        self.future_.add_done_callback(
            partial(
                self.responseKillCallback,
                turtle_name=turtle_name
            )
        )

    def responseKillCallback(self, future, turtle_name):
        try:
            future.result()

            for i, turtle in enumerate(self.alive_turtles_):
                if turtle.name == turtle_name:
                    del self.alive_turtles_[i]
                    self.aliveTurtles()
                    break

        except Exception as e:
            self.get_logger().error(
                "Service call failed %r" % (e,)
            )


def main(args=None):
    rclpy.init(args=args)
    turtle_spawner = TurtleSpawner()
    rclpy.spin(turtle_spawner)
    turtle_spawner.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
