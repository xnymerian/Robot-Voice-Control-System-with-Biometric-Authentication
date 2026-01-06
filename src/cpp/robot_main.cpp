#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <thread>
#include <atomic>
#include <chrono>

// --- CONFIGURATION ---
#define MOTION_IP "192.168.1.120" // Robot IP address (192.168.1.120 or 192.168.2.1)
#define MOTION_PORT 43893         
#define LISTEN_PORT 5001          

// --- PROTOCOL STRUCTURES ---
struct CommandHead {
    uint32_t code;
    uint32_t parameters_size;
    uint32_t type;
};

const uint32_t kDataSize = 256;
struct Command {
    CommandHead head;
    uint32_t data[kDataSize];
};

// --- COMMAND CODES FROM DOCUMENTATION ---
const uint32_t CMD_HEARTBEAT     = 0x21040001; // [cite: 1876]
const uint32_t CMD_STAND_SIT     = 0x21010202; // [cite: 1917] Stand/Sit Toggle
const uint32_t CMD_MOVE_MODE     = 0x21010D06; //  Move Mode (Walking Mode)
const uint32_t CMD_NAV_MODE      = 0x21010C03; //  Navigation Mode (Listen to PC Mode)
const uint32_t CMD_VEL_X         = 0x0140;     // [cite: 1996] X Velocity (Forward/Backward)
const uint32_t CMD_HELLO         = 0x21010507; // [cite: 1948] Hello/Greeting

// Global Variables
int sockfd;
struct sockaddr_in motion_addr;
std::atomic<double> target_velocity_x(0.0); 
std::atomic<bool> is_moving(false);         

// --- HELPER FUNCTIONS ---
void send_simple_cmd(uint32_t code, uint32_t value = 0) {
    CommandHead cmd = {0};
    cmd.code = code;
    cmd.parameters_size = value; 
    cmd.type = 0;                
    sendto(sockfd, &cmd, sizeof(cmd), 0, (struct sockaddr*)&motion_addr, sizeof(motion_addr));
}

void send_complex_cmd_double(uint32_t code, double value) {
    Command cmd = {0};
    cmd.head.code = code;
    cmd.head.parameters_size = sizeof(double); 
    cmd.head.type = 1;                         
    memcpy(cmd.data, &value, sizeof(double));
    sendto(sockfd, &cmd, sizeof(CommandHead) + cmd.head.parameters_size, 0, 
           (struct sockaddr*)&motion_addr, sizeof(motion_addr));
}

// --- CONTROL LOOP (50Hz) ---
void control_loop() {
    while (true) {
        // 1. Heartbeat (Required)
        send_simple_cmd(CMD_HEARTBEAT, 0);

        // 2. If moving, continuously send velocity data
        if (is_moving) {
            send_complex_cmd_double(CMD_VEL_X, target_velocity_x.load());
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(20)); 
    }
}

int main() {
    // 1. UDP Socket Setup
    if ((sockfd = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
        perror("Socket error");
        return -1;
    }

    memset(&motion_addr, 0, sizeof(motion_addr));
    motion_addr.sin_family = AF_INET;
    motion_addr.sin_port = htons(MOTION_PORT);
    motion_addr.sin_addr.s_addr = inet_addr(MOTION_IP);

    struct sockaddr_in server_addr, client_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(LISTEN_PORT);

    if (bind(sockfd, (const struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Bind error");
        return -1;
    }

    std::cout << "Lite3 Controller (Documentation Approved V3) Started!" << std::endl;
    
    std::thread ctrl_thread(control_loop);
    ctrl_thread.detach();

    char buffer[1024];
    socklen_t addr_len = sizeof(client_addr);

    while (true) {
        int n = recvfrom(sockfd, (char *)buffer, 1024, MSG_WAITALL, 
                         (struct sockaddr *)&client_addr, &addr_len);
        
        if (n > 0) {
            char command = buffer[0];
            std::cout << "Received Command: " << command << std::endl;

            switch (command) {
                case 'K': // STAND UP (or Sit)
                    std::cout << ">>> COMMAND: Stand/Sit Toggle" << std::endl;
                    is_moving = false; 
                    target_velocity_x = 0.0;
                    // Switch to Navigation Mode before standing to listen for commands
                    send_simple_cmd(CMD_NAV_MODE, 0); 
                    usleep(50000); 
                    send_simple_cmd(CMD_STAND_SIT, 0);
                    break;
                
                case 'O': // SIT DOWN (Same command toggles in documentation)
                     std::cout << ">>> COMMAND: Sit (Stand/Sit Toggle)" << std::endl;
                     is_moving = false;
                     target_velocity_x = 0.0;
                     send_simple_cmd(CMD_STAND_SIT, 0);
                     break;

                case 'I': // FORWARD
                    std::cout << ">>> COMMAND: Move Forward (Preparing...)" << std::endl;
                    
                    // STEP 1: Switch to Navigation Mode (Listen to me)
                    send_simple_cmd(CMD_NAV_MODE, 0); 
                    usleep(50000); // Wait 50ms

                    // STEP 2: Switch to Move Mode (Walking mode)
                    send_simple_cmd(CMD_MOVE_MODE, 0);
                    usleep(50000);

                    // STEP 3: Set velocity and start loop
                    target_velocity_x = 0.3; // 0.3 m/s forward
                    is_moving = true;
                    std::cout << ">>> Setting velocity: 0.3 m/s" << std::endl;
                    break;

                case 'G': // BACKWARD
                    std::cout << ">>> COMMAND: Move Backward" << std::endl;
                    send_simple_cmd(CMD_NAV_MODE, 0);
                    usleep(50000);
                    send_simple_cmd(CMD_MOVE_MODE, 0);
                    usleep(50000);
                    
                    target_velocity_x = -0.3; // Negative velocity = Backward
                    is_moving = true;
                    break;
                
                case '0': // STOP
                    std::cout << ">>> COMMAND: Stop" << std::endl;
                    target_velocity_x = 0.0;
                    is_moving = false; 
                    // Manually send 0 velocity once to ensure stop
                    send_complex_cmd_double(CMD_VEL_X, 0.0);
                    break;

                case 'H': // HELLO
                    std::cout << ">>> COMMAND: Hello (Works when sitting)" << std::endl;
                    is_moving = false;
                    send_simple_cmd(CMD_HELLO, 0);
                    break;
            }
        }
    }
    return 0;
}