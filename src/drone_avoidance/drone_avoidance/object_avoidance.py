import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import LaserScan

class WallFollowingObstacleAvoidance(Node):
    def __init__(self):
        super().__init__('wall_following_obstacle_avoidance')
        self.cmd_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.scan_sub = self.create_subscription(LaserScan, 'scan', self.scan_callback, 10)
        self.twist = Twist()
        self.avoiding_obstacle = False  # Flag to track if we are actively avoiding an obstacle
        self.following_wall = False  # Flag to indicate wall-following mode
        self.initial_heading = 0.0  # Track initial heading for realignment

    def scan_callback(self, msg):
        # Define three regions based on the laser scan ranges
        left_distances = msg.ranges[45:135]  # Left side
        front_distances = msg.ranges[0:45]  # Front
        right_distances = msg.ranges[135:179]  # Right side

        # Calculate the minimum distance in each region
        min_left = min(left_distances) if left_distances else float('inf')
        min_front = min(front_distances) if front_distances else float('inf')
        min_right = min(right_distances) if right_distances else float('inf')

        # Logging the distances for debugging
        self.get_logger().info(f'Left: {min_left}, Front: {min_front}, Right: {min_right}')

        # Threshold distance for obstacle avoidance
        obstacle_distance = 1.0
        wall_following_distance = 0.5  # Desired distance to maintain from the left wall

        if min_front <= obstacle_distance:
            # If an obstacle is detected in front, start avoidance by turning right
            if not self.avoiding_obstacle:
                self.initial_heading = self.twist.angular.z  # Save the initial heading
                self.get_logger().info(f'Setting initial heading: {self.initial_heading}')
                
            self.avoiding_obstacle = True
            self.following_wall = True  # Start wall-following behavior
            self.twist.linear.x = 0.0
            self.twist.angular.z = -0.5  # Turn right

        elif self.avoiding_obstacle and self.following_wall:
            # Maintain a set distance from the left wall (obstacle) during wall-following mode
            if min_left <= wall_following_distance:
                # If too close to the wall, turn slightly right
                self.twist.linear.x = 0.3
                self.twist.angular.z = -0.2
            elif min_left > wall_following_distance:
                # If too far from the wall, turn slightly left
                self.twist.linear.x = 0.3
                self.twist.angular.z = 0.2
            else:
                # Move forward if at the correct distance
                self.twist.linear.x = 0.3
                self.twist.angular.z = 0.0

            # Check if it's clear to stop wall-following
            if min_front > obstacle_distance and min_left > obstacle_distance:
                self.avoiding_obstacle = False
                self.following_wall = False
                self.twist.angular.z = self.initial_heading  # Return to initial heading

        else:
            # Move forward normally when no obstacles are detected
            self.twist.linear.x = 0.3
            self.twist.angular.z = 0.0

        # Publish the command
        self.cmd_pub.publish(self.twist)
        # Log avoidance state for debugging
        self.get_logger().info(f'Avoiding Obstacle: {self.avoiding_obstacle}, Following Wall: {self.following_wall}')

def main(args=None):
    rclpy.init(args=args)
    node = WallFollowingObstacleAvoidance()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
