cmake_minimum_required(VERSION 3.14)

project(YourProjectName)

# Enable testing
enable_testing()

# FetchContent to download Google Test
include(FetchContent)
FetchContent_Declare(
    gtest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG release-1.11.0  # You can change the tag or branch name as needed
)
FetchContent_MakeAvailable(gtest)

# Create a test executable
add_executable(tests test_main.cpp)  # Replace with your test file

# Link Google Test libraries
target_link_libraries(tests gtest gtest_main)

# Add tests discovery
add_test(NAME TestYourTests COMMAND tests)  # Replace with the name of your tests

# Instructions for running tests:
# To build the tests, run:
#     cmake --build .
#     Then, run the tests using:
#     ctest -C Debug  # Adjust configuration name if needed
