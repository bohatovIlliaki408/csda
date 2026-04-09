cmake_minimum_required(VERSION 3.14)

project(csda)

enable_testing()

include(FetchContent)

FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG main
)

FetchContent_MakeAvailable(googletest)

add_executable(hello main.cpp)

add_executable(unit_tests
    tests/unit_tests.cpp
    math_operations.cpp
)

target_link_libraries(unit_tests gtest gtest_main)

add_test(NAME BasicAddition COMMAND unit_tests)
