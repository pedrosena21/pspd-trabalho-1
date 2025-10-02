cmake_minimum_required(VERSION 3.15)
project(BingoStub)

set(CMAKE_CXX_STANDARD 17)

find_package(Protobuf REQUIRED)
find_package(gRPC CONFIG REQUIRED)

set(PROTO_PATH "${CMAKE_CURRENT_SOURCE_DIR}/../proto")
set(GENERATED_PATH "${CMAKE_CURRENT_SOURCE_DIR}/generated")

file(MAKE_DIRECTORY ${GENERATED_PATH})

add_custom_command(
    OUTPUT "${GENERATED_PATH}/bingo.pb.cc"
           "${GENERATED_PATH}/bingo.grpc.pb.cc"
    COMMAND protoc
    ARGS --grpc_out=${GENERATED_PATH}
         --cpp_out=${GENERATED_PATH}
         -I${PROTO_PATH}
         --plugin=protoc-gen-grpc=`which grpc_cpp_plugin`
         ${PROTO_PATH}/bingo.proto
    DEPENDS ${PROTO_PATH}/bingo.proto
)

add_library(bingo_proto
    ${GENERATED_PATH}/bingo.pb.cc
    ${GENERATED_PATH}/bingo.grpc.pb.cc
)

target_link_libraries(bingo_proto
    gRPC::grpc++
    protobuf::libprotobuf
)

add_executable(bingo_stub_server server.cpp)

target_link_libraries(bingo_stub_server
    bingo_proto
    gRPC::grpc++
    protobuf::libprotobuf
)
