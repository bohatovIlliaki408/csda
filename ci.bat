@echo off

echo Create build folder
if not exist build mkdir build
cd build

echo Run cmake
cmake ..

echo Build project
cmake --build . --config Debug

echo Run tests
ctest -C Debug --output-on-failure

pause
