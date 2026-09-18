from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    turtlesim_node = Node(
        package="turtlesim",
        executable="turtlesim_node",
        name="turtlesim"
    )

    turtle_spawner_node = Node(
        package="turtlesim_catch_them_all",
        executable="turtle_spawner",
        name="turtle_spawner",
        parameters=[
            {
                "frequency": 1.0,
                "prefix": "my_turtle",
                "counter": 0
            }
        ],
        output="screen"
    )

    turtle_controller_node = Node(
        package="turtlesim_catch_them_all",
        executable="turtle_controller",
        name="turtle_controller",
        parameters=[
            {
                "frequency": 100.0,
                "catch_closest_turtle_first": True
            }
        ],
        output="screen"
    )

    return LaunchDescription([
        turtlesim_node,
        turtle_spawner_node,
        turtle_controller_node
    ])
