cmake_minimum_required(VERSION 3.15)
project(BingoGrpcStub VERSION 1.0 LANGUAGES CXX)

# C++17 padrão
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Flags de compilação
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Wall -Wextra")
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -g -O0")
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3")

# Encontrar pacotes necessários
find_package(Threads REQUIRED)
find_package(Protobuf REQUIRED)
find_package(gRPC CONFIG REQUIRED)

# Mensagens de debug
message(STATUS "Protobuf version: ${Protobuf_VERSION}")
message(STATUS "Protobuf libraries: ${Protobuf_LIBRARIES}")
message(STATUS "gRPC found: ${gRPC_FOUND}")

# Diretórios
set(GENERATED_DIR ${CMAKE_CURRENT_SOURCE_DIR}/generated)

# Diretórios de inclusão
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${GENERATED_DIR}
    ${Protobuf_INCLUDE_DIRS}
)

# Arquivos gerados pelo protoc (já devem existir via generate_grpc.sh)
set(PROTO_SRCS
    ${GENERATED_DIR}/bingo.pb.cc
    ${GENERATED_DIR}/bingo.grpc.pb.cc
)
set(PROTO_HDRS
    ${GENERATED_DIR}/bingo.pb.h
    ${GENERATED_DIR}/bingo.grpc.pb.h
)

# Verificar se os arquivos proto foram gerados
if(NOT EXISTS ${GENERATED_DIR}/bingo.pb.cc)
    message(WARNING "Arquivos protobuf não encontrados em ${GENERATED_DIR}")
    message(WARNING "Execute './generate_grpc.sh' na raiz do projeto primeiro!")
endif()

# Biblioteca com os arquivos protobuf gerados
add_library(bingo_proto ${PROTO_SRCS})
target_link_libraries(bingo_proto
    PUBLIC
        ${Protobuf_LIBRARIES}
        gRPC::grpc++
        gRPC::grpc++_reflection
)
target_include_directories(bingo_proto
    PUBLIC
        ${GENERATED_DIR}
        ${Protobuf_INCLUDE_DIRS}
)

# Executável principal - Stub C++
add_executable(bingo_stub
    server.cpp
)

target_link_libraries(bingo_stub
    PRIVATE
        bingo_proto
        gRPC::grpc++
        gRPC::grpc++_reflection
        ${Protobuf_LIBRARIES}
        Threads::Threads
)

# Opções de instalação
install(TARGETS bingo_stub
    RUNTIME DESTINATION bin
)

# Informações de build
message(STATUS "")
message(STATUS "==========================================")
message(STATUS "  Bingo gRPC Stub - Configuração CMake")
message(STATUS "==========================================")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "C++ standard: C++${CMAKE_CXX_STANDARD}")
message(STATUS "Source directory: ${CMAKE_CURRENT_SOURCE_DIR}")
message(STATUS "Generated files: ${GENERATED_DIR}")
message(STATUS "==========================================")
message(STATUS "")

# Target para executar
add_custom_target(run
    COMMAND ${CMAKE_CURRENT_BINARY_DIR}/bingo_stub
    DEPENDS bingo_stub
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/..
    COMMENT "Executando bingo_stub"
)

# Help target
add_custom_target(help-targets
    COMMAND ${CMAKE_COMMAND} -E echo ""
    COMMAND ${CMAKE_COMMAND} -E echo "Targets disponíveis:"
    COMMAND ${CMAKE_COMMAND} -E echo "  make               - Compila o projeto"
    COMMAND ${CMAKE_COMMAND} -E echo "  make bingo_stub    - Compila apenas o stub"
    COMMAND ${CMAKE_COMMAND} -E echo "  make run           - Executa o stub"
    COMMAND ${CMAKE_COMMAND} -E echo "  make clean         - Limpa arquivos de build"
    COMMAND ${CMAKE_COMMAND} -E echo "  make install       - Instala o executável"
    COMMAND ${CMAKE_COMMAND} -E echo ""
    COMMAND ${CMAKE_COMMAND} -E echo "IMPORTANTE: Execute '../generate_grpc.sh' antes de compilar!"
    COMMAND ${CMAKE_COMMAND} -E echo ""
)
