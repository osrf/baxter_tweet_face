cmake_minimum_required(VERSION 2.8.3)
project(baxter_tweet_face)

find_package(catkin REQUIRED)

catkin_python_setup()

catkin_package()

install(PROGRAMS baxter_tweet_face.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION})
