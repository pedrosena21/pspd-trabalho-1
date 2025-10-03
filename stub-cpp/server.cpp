#include <iostream>
#include <memory>
#include <string>
#include <sstream>
#include <vector>
#include <cstring>
#include <grpcpp/grpcpp.h>

// Headers gerados
#include "bingo.grpc.pb.h"

// Socket includes para servidor HTTP básico
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <signal.h>

using grpc::Channel;
using grpc::ClientContext;
using grpc::Status;

volatile sig_atomic_t keep_running = 1;

void signal_handler(int signum) {
    std::cout << "\n[STUB] Recebido sinal " << signum << ", encerrando..." << std::endl;
    keep_running = 0;
}

class BingoStub {
private:
    std::unique_ptr<bingo::GameService::Stub> game_stub_;
    std::unique_ptr<bingo::ValidationService::Stub> validation_stub_;

public:
    BingoStub(std::shared_ptr<Channel> game_channel,
              std::shared_ptr<Channel> validation_channel)
        : game_stub_(bingo::GameService::NewStub(game_channel)),
          validation_stub_(bingo::ValidationService::NewStub(validation_channel)) {

        // Testa conectividade
        auto game_state = game_channel->GetState(true);
        auto validation_state = validation_channel->GetState(true);

        std::cout << "[STUB] Estado GameService: " << game_state << std::endl;
        std::cout << "[STUB] Estado ValidationService: " << validation_state << std::endl;
        std::cout << "[STUB] ✓ Stubs criados" << std::endl;
    }

    // Cria um novo jogo
    std::string CreateGame(const std::string& game_name) {
        bingo::CreateGameRequest request;
        request.set_game_name(game_name);

        bingo::CreateGameResponse response;
        ClientContext context;

        Status status = game_stub_->CreateGame(&context, request, &response);

        if (status.ok()) {
            std::cout << "[STUB] ✓ Jogo criado: " << response.game_id() << std::endl;
            return response.game_id();
        } else {
            std::cerr << "[STUB] ✗ Erro ao criar jogo: " << status.error_message() << std::endl;
            return "";
        }
    }

    // Registra um jogador
    struct PlayerInfo {
        std::string player_id;
        std::vector<int32_t> card;
        bool success;
    };

    PlayerInfo RegisterPlayer(const std::string& game_id, const std::string& player_name) {
        bingo::RegisterPlayerRequest request;
        request.set_game_id(game_id);
        request.set_player_name(player_name);

        bingo::RegisterPlayerResponse response;
        ClientContext context;
        context.set_deadline(std::chrono::system_clock::now() + std::chrono::seconds(5));

        std::cout << "[STUB] Chamando RegisterPlayer(game_id=" << game_id
                  << ", player_name=" << player_name << ")" << std::endl;

        Status status = game_stub_->RegisterPlayer(&context, request, &response);

        PlayerInfo result;
        result.success = false;

        std::cout << "[STUB] Status gRPC: ok=" << status.ok()
                  << ", code=" << status.error_code()
                  << ", msg='" << status.error_message() << "'" << std::endl;

        if (status.ok()) {
            std::cout << "[STUB] Response: success=" << response.success()
                      << ", player_id=" << response.player_id()
                      << ", card_size=" << response.card_numbers_size() << std::endl;
        }

        if (status.ok() && response.success()) {
            result.player_id = response.player_id();
            result.success = true;

            for (int i = 0; i < response.card_numbers_size(); ++i) {
                result.card.push_back(response.card_numbers(i));
            }

            std::cout << "[STUB] ✓ Jogador registrado: " << player_name
                      << " (ID: " << result.player_id << ")" << std::endl;
            std::cout << "[STUB]   Cartela (" << result.card.size() << " números): ";
            for (size_t i = 0; i < result.card.size() && i < 10; ++i) {
                std::cout << result.card[i] << " ";
            }
            if (result.card.size() > 10) std::cout << "...";
            std::cout << std::endl;
        } else {
            std::cerr << "[STUB] ✗ Erro ao registrar jogador: "
                      << status.error_message() << std::endl;
        }

        return result;
    }

    // Sorteia um número
    struct DrawResult {
        int32_t number;
        bool success;
    };

    DrawResult DrawNumber(const std::string& game_id) {
        bingo::DrawNumberRequest request;
        request.set_game_id(game_id);

        bingo::DrawNumberResponse response;
        ClientContext context;
        context.set_deadline(std::chrono::system_clock::now() + std::chrono::seconds(5));

        Status status = game_stub_->DrawNumber(&context, request, &response);

        DrawResult result;
        result.success = false;
        result.number = 0;

        if (status.ok() && response.success()) {
            result.number = response.number();
            result.success = true;
            std::cout << "[STUB] 🎲 Número sorteado: " << result.number << std::endl;
        } else {
            if (!status.ok()) {
                std::cerr << "[STUB] ✗ Erro gRPC ao sortear: " << status.error_message() << std::endl;
            } else {
                std::cerr << "[STUB] ✗ Sorteio falhou (success=false)" << std::endl;
            }
        }

        return result;
    }

    // Marca um número
    bool MarkNumber(const std::string& game_id, const std::string& player_id, int32_t number) {
        bingo::MarkNumberRequest request;
        request.set_game_id(game_id);
        request.set_player_id(player_id);
        request.set_number(number);

        bingo::MarkNumberResponse response;
        ClientContext context;

        Status status = game_stub_->MarkNumber(&context, request, &response);

        if (status.ok() && response.success()) {
            std::cout << "[STUB] ✓ Número " << number << " marcado para "
                      << player_id << std::endl;
            return true;
        } else {
            std::cout << "[STUB] ✗ Número " << number
                      << " inválido ou não está na cartela" << std::endl;
            return false;
        }
    }

    // Verifica BINGO
    bool CheckBingo(const std::string& game_id, const std::string& player_id) {
        bingo::CheckBingoRequest request;
        request.set_game_id(game_id);
        request.set_player_id(player_id);

        bingo::CheckBingoResponse response;
        ClientContext context;

        Status status = game_stub_->CheckBingo(&context, request, &response);

        if (status.ok()) {
            if (response.bingo()) {
                std::cout << "[STUB] 🎉 BINGO CONFIRMADO para " << player_id << "!" << std::endl;
            } else {
                std::cout << "[STUB] ✗ Bingo inválido para " << player_id << std::endl;
            }
            return response.bingo();
        } else {
            std::cerr << "[STUB] ✗ Erro ao verificar bingo: "
                      << status.error_message() << std::endl;
            return false;
        }
    }

    // Obtém cartela via ValidationService
    std::vector<int32_t> GetCard(const std::string& player_id) {
        bingo::GetCardRequest request;
        request.set_player_id(player_id);

        bingo::GetCardResponse response;
        ClientContext context;

        Status status = validation_stub_->GetCard(&context, request, &response);

        std::vector<int32_t> card;
        if (status.ok()) {
            for (int i = 0; i < response.card_numbers_size(); ++i) {
                card.push_back(response.card_numbers(i));
            }
        }

        return card;
    }
};

// Funções auxiliares para parsing JSON simples
std::string parseJsonString(const std::string& json, const std::string& key) {
    std::string search = "\"" + key + "\"";
    size_t pos = json.find(search);
    if (pos == std::string::npos) return "";

    pos += search.length();

    // Pula espaços e ':'
    while (pos < json.length() && (json[pos] == ' ' || json[pos] == ':')) {
        pos++;
    }

    // Deve começar com "
    if (pos >= json.length() || json[pos] != '"') return "";
    pos++; // pula a "

    size_t end = json.find("\"", pos);
    if (end == std::string::npos) return "";

    return json.substr(pos, end - pos);
}

int parseJsonInt(const std::string& json, const std::string& key) {
    std::string search = "\"" + key + "\":";
    size_t pos = json.find(search);
    if (pos == std::string::npos) return 0;

    pos += search.length();
    while (pos < json.length() && isspace(json[pos])) pos++;

    size_t end = pos;
    while (end < json.length() && (isdigit(json[end]) || json[end] == '-')) {
        end++;
    }

    if (pos == end) return 0;
    std::string numStr = json.substr(pos, end - pos);
    return std::stoi(numStr);
}

std::string vectorToJson(const std::vector<int32_t>& vec) {
    std::ostringstream oss;
    oss << "[";
    for (size_t i = 0; i < vec.size(); ++i) {
        oss << vec[i];
        if (i < vec.size() - 1) oss << ",";
    }
    oss << "]";
    return oss.str();
}

std::string escapeJson(const std::string& s) {
    std::ostringstream o;
    for (char c : s) {
        switch (c) {
            case '"': o << "\\\""; break;
            case '\\': o << "\\\\"; break;
            case '\n': o << "\\n"; break;
            case '\r': o << "\\r"; break;
            case '\t': o << "\\t"; break;
            default: o << c; break;
        }
    }
    return o.str();
}

// Mini servidor HTTP
class SimpleHttpServer {
private:
    int server_fd_;
    BingoStub& stub_;

    std::string handleRequest(const std::string& method, const std::string& path,
                             const std::string& body) {
        std::cout << "\n[HTTP] " << method << " " << path << std::endl;
        if (!body.empty() && body.length() < 200) {
            std::cout << "[HTTP] Body: " << body << std::endl;
        }

        // Página inicial
        if (method == "GET" && path == "/") {
            return "HTTP/1.1 200 OK\r\n"
                   "Content-Type: text/html; charset=utf-8\r\n"
                   "\r\n"
                   "<!DOCTYPE html><html><head>"
                   "<title>Bingo gRPC Stub</title>"
                   "<style>body{font-family:Arial;margin:40px;}"
                   "h1{color:#333;}.endpoint{background:#f4f4f4;padding:15px;"
                   "margin:10px 0;border-left:4px solid #007bff;}"
                   "code{background:#e0e0e0;padding:2px 6px;border-radius:3px;}</style>"
                   "</head><body>"
                   "<h1>🎮 Bingo gRPC API Gateway</h1>"
                   "<p>Stub C++ conectado aos serviços Python via gRPC</p>"
                   "<h2>Endpoints Disponíveis:</h2>"
                   "<div class='endpoint'><b>POST /game/create</b><br>"
                   "Cria um novo jogo<br>"
                   "<code>{\"game_name\":\"Meu Bingo\"}</code></div>"
                   "<div class='endpoint'><b>POST /game/register</b><br>"
                   "Registra um jogador<br>"
                   "<code>{\"game_id\":\"...\",\"player_name\":\"Alice\"}</code></div>"
                   "<div class='endpoint'><b>POST /game/draw</b><br>"
                   "Sorteia um número<br>"
                   "<code>{\"game_id\":\"...\"}</code></div>"
                   "<div class='endpoint'><b>POST /game/mark</b><br>"
                   "Marca um número na cartela<br>"
                   "<code>{\"game_id\":\"...\",\"player_id\":\"...\",\"number\":42}</code></div>"
                   "<div class='endpoint'><b>POST /game/bingo</b><br>"
                   "Declara BINGO<br>"
                   "<code>{\"game_id\":\"...\",\"player_id\":\"...\"}</code></div>"
                   "<div class='endpoint'><b>GET /game/card?player_id=...</b><br>"
                   "Obtém cartela do jogador</div>"
                   "</body></html>";
        }

        // Criar jogo
        if (method == "POST" && path == "/game/create") {
            std::string game_name = parseJsonString(body, "game_name");
            if (game_name.empty()) game_name = "Bingo Game";

            std::string game_id = stub_.CreateGame(game_name);

            std::ostringstream response;
            response << "{\"game_id\":\"" << escapeJson(game_id) << "\","
                    << "\"success\":" << (!game_id.empty() ? "true" : "false") << "}";

            return "HTTP/1.1 200 OK\r\n"
                   "Content-Type: application/json\r\n"
                   "Access-Control-Allow-Origin: *\r\n"
                   "Connection: close\r\n"
                   "\r\n" + response.str();
        }

        // Registrar jogador
        if (method == "POST" && path == "/game/register") {
            std::string game_id = parseJsonString(body, "game_id");
            std::string player_name = parseJsonString(body, "player_name");

            auto result = stub_.RegisterPlayer(game_id, player_name);

            std::ostringstream response;
            response << "{\"player_id\":\"" << escapeJson(result.player_id) << "\","
                    << "\"card\":" << vectorToJson(result.card) << ","
                    << "\"success\":" << (result.success ? "true" : "false") << "}";

            return "HTTP/1.1 200 OK\r\n"
                   "Content-Type: application/json\r\n"
                   "Access-Control-Allow-Origin: *\r\n"
                   "Connection: close\r\n"
                   "\r\n" + response.str();
        }

        // Sortear número
        if (method == "POST" && path == "/game/draw") {
            std::string game_id = parseJsonString(body, "game_id");

            auto result = stub_.DrawNumber(game_id);

            std::ostringstream response;
            response << "{\"number\":" << result.number << ","
                    << "\"success\":" << (result.success ? "true" : "false") << "}";

            return "HTTP/1.1 200 OK\r\n"
                   "Content-Type: application/json\r\n"
                   "Access-Control-Allow-Origin: *\r\n"
                   "Connection: close\r\n"
                   "\r\n" + response.str();
        }

        // Marcar número
        if (method == "POST" && path == "/game/mark") {
            std::string game_id = parseJsonString(body, "game_id");
            std::string player_id = parseJsonString(body, "player_id");
            int number = parseJsonInt(body, "number");

            bool success = stub_.MarkNumber(game_id, player_id, number);

            std::ostringstream response;
            response << "{\"success\":" << (success ? "true" : "false") << "}";

            return "HTTP/1.1 200 OK\r\n"
                   "Content-Type: application/json\r\n"
                   "Access-Control-Allow-Origin: *\r\n"
                   "Connection: close\r\n"
                   "\r\n" + response.str();
        }

        // Verificar BINGO
        if (method == "POST" && path == "/game/bingo") {
            std::string game_id = parseJsonString(body, "game_id");
            std::string player_id = parseJsonString(body, "player_id");

            bool bingo = stub_.CheckBingo(game_id, player_id);

            std::ostringstream response;
            response << "{\"bingo\":" << (bingo ? "true" : "false") << "}";

            return "HTTP/1.1 200 OK\r\n"
                   "Content-Type: application/json\r\n"
                   "Access-Control-Allow-Origin: *\r\n"
                   "Connection: close\r\n"
                   "\r\n" + response.str();
        }

        // Obter cartela (GET)
        if (method == "GET" && path.find("/game/card") == 0) {
            size_t pos = path.find("player_id=");
            if (pos != std::string::npos) {
                std::string player_id = path.substr(pos + 10);
                auto card = stub_.GetCard(player_id);

                std::ostringstream response;
                response << "{\"player_id\":\"" << escapeJson(player_id) << "\","
                        << "\"card\":" << vectorToJson(card) << "}";

                return "HTTP/1.1 200 OK\r\n"
                       "Content-Type: application/json\r\n"
                       "Access-Control-Allow-Origin: *\r\n"
                       "Connection: close\r\n"
                       "\r\n" + response.str();
            }
        }

        // 404 Not Found
        return "HTTP/1.1 404 Not Found\r\n"
               "Content-Type: application/json\r\n"
               "\r\n"
               "{\"error\":\"Endpoint not found\"}";
    }

public:
    SimpleHttpServer(BingoStub& stub) : stub_(stub), server_fd_(-1) {}

    bool start(int port) {
        server_fd_ = socket(AF_INET, SOCK_STREAM, 0);
        if (server_fd_ < 0) {
            std::cerr << "[HTTP] ✗ Erro ao criar socket" << std::endl;
            return false;
        }

        int opt = 1;
        setsockopt(server_fd_, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

        sockaddr_in address;
        address.sin_family = AF_INET;
        address.sin_addr.s_addr = INADDR_ANY;
        address.sin_port = htons(port);

        if (bind(server_fd_, (struct sockaddr*)&address, sizeof(address)) < 0) {
            std::cerr << "[HTTP] ✗ Erro ao fazer bind na porta " << port << std::endl;
            close(server_fd_);
            return false;
        }

        if (listen(server_fd_, 10) < 0) {
            std::cerr << "[HTTP] ✗ Erro ao escutar" << std::endl;
            close(server_fd_);
            return false;
        }

        std::cout << "\n" << std::string(60, '=') << std::endl;
        std::cout << "🌐 STUB gRPC C++ - API GATEWAY RODANDO" << std::endl;
        std::cout << std::string(60, '=') << std::endl;
        std::cout << "REST API: http://localhost:" << port << std::endl;
        std::cout << "GameService: localhost:50051" << std::endl;
        std::cout << "ValidationService: localhost:50052" << std::endl;
        std::cout << "Status: ✓ Online" << std::endl;
        std::cout << std::string(60, '=') << std::endl;
        std::cout << "\nPressione Ctrl+C para encerrar\n" << std::endl;

        while (keep_running) {
            fd_set read_fds;
            FD_ZERO(&read_fds);
            FD_SET(server_fd_, &read_fds);

            struct timeval timeout;
            timeout.tv_sec = 1;
            timeout.tv_usec = 0;

            int activity = select(server_fd_ + 1, &read_fds, NULL, NULL, &timeout);

            if (activity < 0 || !keep_running) break;
            if (activity == 0) continue;

            int client_socket = accept(server_fd_, nullptr, nullptr);
            if (client_socket < 0) continue;

            char buffer[8192] = {0};
            ssize_t bytes_read = read(client_socket, buffer, sizeof(buffer) - 1);

            if (bytes_read > 0) {
                std::string request(buffer, bytes_read);
                std::istringstream iss(request);
                std::string method, path;
                iss >> method >> path;

                std::string body;
                size_t body_pos = request.find("\r\n\r\n");
                if (body_pos != std::string::npos) {
                    body = request.substr(body_pos + 4);
                    // Remove possível lixo no final do body
                    if (!body.empty()) {
                        size_t content_length = 0;
                        size_t cl_pos = request.find("Content-Length:");
                        if (cl_pos != std::string::npos) {
                            std::string cl_line = request.substr(cl_pos);
                            size_t nl_pos = cl_line.find("\r\n");
                            if (nl_pos != std::string::npos) {
                                std::string cl_value = cl_line.substr(15, nl_pos - 15);
                                // Remove espaços
                                cl_value.erase(0, cl_value.find_first_not_of(" \t"));
                                content_length = std::stoul(cl_value);
                                if (body.length() > content_length) {
                                    body = body.substr(0, content_length);
                                }
                            }
                        }
                    }
                }

                std::string response = handleRequest(method, path, body);
                write(client_socket, response.c_str(), response.length());
            }

            close(client_socket);
        }

        close(server_fd_);
        return true;
    }

    ~SimpleHttpServer() {
        if (server_fd_ >= 0) {
            close(server_fd_);
        }
    }
};

int main(int argc, char** argv) {
    // Configurar signal handler
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    // Parâmetros padrão
    std::string game_service_addr = "localhost:50051";
    std::string validation_service_addr = "localhost:50052";
    int http_port = 8080;

    // Parse argumentos
    for (int i = 1; i < argc; i++) {
        std::string arg(argv[i]);
        if (arg == "--game-service" && i + 1 < argc) {
            game_service_addr = argv[++i];
        } else if (arg == "--validation-service" && i + 1 < argc) {
            validation_service_addr = argv[++i];
        } else if (arg == "--port" && i + 1 < argc) {
            http_port = std::stoi(argv[++i]);
        } else if (arg == "--help" || arg == "-h") {
            std::cout << "Uso: " << argv[0] << " [opções]\n"
                      << "Opções:\n"
                      << "  --game-service ADDR      Endereço do GameService (padrão: localhost:50051)\n"
                      << "  --validation-service ADDR Endereço do ValidationService (padrão: localhost:50052)\n"
                      << "  --port PORT              Porta HTTP do stub (padrão: 8080)\n"
                      << "  --help, -h               Mostra esta ajuda\n";
            return 0;
        }
    }

    std::cout << "Iniciando Bingo Stub C++..." << std::endl;
    std::cout << "Conectando a:" << std::endl;
    std::cout << "  GameService: " << game_service_addr << std::endl;
    std::cout << "  ValidationService: " << validation_service_addr << std::endl;

    // Criar canais gRPC
    auto game_channel = grpc::CreateChannel(
        game_service_addr, grpc::InsecureChannelCredentials());
    auto validation_channel = grpc::CreateChannel(
        validation_service_addr, grpc::InsecureChannelCredentials());

    // Criar stub
    BingoStub stub(game_channel, validation_channel);

    // Iniciar servidor HTTP
    SimpleHttpServer server(stub);

    if (!server.start(http_port)) {
        std::cerr << "✗ Falha ao iniciar servidor HTTP" << std::endl;
        return 1;
    }

    std::cout << "\n[STUB] Encerrando..." << std::endl;
    return 0;
}
