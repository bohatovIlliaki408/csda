@echo off

mkdir build
cd build

cmake ..
cmake --build .

ctest --output-on-failure
chmod +x ci.sh
./ci.sh
