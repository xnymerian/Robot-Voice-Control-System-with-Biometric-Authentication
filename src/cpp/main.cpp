#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>

// Vosk and PortAudio header files
#include <vosk_api.h>
#include "../../include/portaudio.h"

#define SAMPLE_RATE 16000
#define FRAMES_PER_BUFFER 4000
#define UDP_IP "127.0.0.1"
#define UDP_PORT 5001
#define MODEL_PATH "../../model"

// UDP Command Sending Function
void send_udp_command(int sock, struct sockaddr_in& dest_addr, char command) {
    sendto(sock, &command, 1, 0, (struct sockaddr*)&dest_addr, sizeof(dest_addr));
    std::cout << "Sent to C++: " << command << std::endl;
}

// Simple command analysis function
// Searches within string without JSON library (Faster and simpler)
void process_result(const char* json_result, int sock, struct sockaddr_in& dest_addr) {
    std::string text(json_result);
    
    // Vosk may return empty result, check it
    if (text.empty()) return;

    std::cout << "Detected: " << text << std::endl;

    if (text.find("kalk") != std::string::npos || text.find("ayağa") != std::string::npos) {
        send_udp_command(sock, dest_addr, 'K');
    }
    else if (text.find("otur") != std::string::npos) {
        send_udp_command(sock, dest_addr, 'O');
    }
    else if (text.find("ileri") != std::string::npos || text.find("git") != std::string::npos) {
        // Distinguish forward and backward
        if (text.find("geri") == std::string::npos) { // If it doesn't contain "geri", it's forward
             send_udp_command(sock, dest_addr, 'I');
        }
    }
    else if (text.find("geri") != std::string::npos) {
        send_udp_command(sock, dest_addr, 'G');
    }
    else if (text.find("takip") != std::string::npos || text.find("başla") != std::string::npos) {
        send_udp_command(sock, dest_addr, '1');
    }
    else if (text.find("dur") != std::string::npos || text.find("bekle") != std::string::npos) {
        send_udp_command(sock, dest_addr, '0');
    }
}

int main() {
    // --- 1. UDP SOCKET SETUP ---
    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        std::cerr << "Socket creation failed!" << std::endl;
        return -1;
    }
    
    struct sockaddr_in dest_addr;
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(UDP_PORT);
    dest_addr.sin_addr.s_addr = inet_addr(UDP_IP);

    // --- 2. VOSK MODEL LOADING ---
    std::cout << "Loading model (model directory)..." << std::endl;
    VoskModel *model = vosk_model_new(MODEL_PATH);
    if (model == nullptr) {
        std::cerr << "ERROR: '" << MODEL_PATH << "' directory not found or model is invalid!" << std::endl;
        return -1;
    }
    VoskRecognizer *recognizer = vosk_recognizer_new(model, SAMPLE_RATE);

    // --- 3. MICROPHONE (PORTAUDIO) SETTINGS ---
    PaError err = Pa_Initialize();
    if (err != paNoError) {
        std::cerr << "PortAudio error: " << Pa_GetErrorText(err) << std::endl;
        return -1;
    }

    PaStream *stream;
    err = Pa_OpenDefaultStream(&stream,
                               1,          // Input channel (Mono)
                               0,          // Output channel (None)
                               paInt16,    // Format (16 bit integer)
                               SAMPLE_RATE,
                               FRAMES_PER_BUFFER,
                               NULL,       // No callback, we'll do blocking read
                               NULL);

    if (err != paNoError) {
        std::cerr << "Stream opening error: " << Pa_GetErrorText(err) << std::endl;
        return -1;
    }

    err = Pa_StartStream(stream);
    if (err != paNoError) {
        std::cerr << "Stream starting error: " << Pa_GetErrorText(err) << std::endl;
        return -1;
    }

    std::cout << "\nOFFLINE MODE READY! (C++ Version)" << std::endl;
    std::cout << "Commands: Kalk, Otur, İleri, Geri, Takip, Dur" << std::endl;

    // --- 4. MAIN LOOP ---
    int16_t buffer[FRAMES_PER_BUFFER];
    
    while (true) {
        // Read from microphone
        err = Pa_ReadStream(stream, buffer, FRAMES_PER_BUFFER);
        if (err != paNoError && err != paInputOverflowed) {
            std::cerr << "Read error!" << std::endl;
            break; 
        }

        // Send to Vosk (C API requires int16 data as char*)
        if (vosk_recognizer_accept_waveform(recognizer, (const char *)buffer, FRAMES_PER_BUFFER * 2)) {
            // Get result when complete sentence is finished
            const char *result = vosk_recognizer_result(recognizer);
            process_result(result, sock, dest_addr);
        } else {
            // Partial result can be obtained if sentence is not finished, but we wait for complete result.
        }
    }

    // --- CLEANUP ---
    Pa_StopStream(stream);
    Pa_CloseStream(stream);
    Pa_Terminate();
    vosk_recognizer_free(recognizer);
    vosk_model_free(model);
    close(sock);

    return 0;
}