#include <algorithm>
#include <atomic>
#include <array>
#include <functional>
#include <memory>
#include <mutex>
#include <condition_variable>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <stdexcept>
#include <string>
#include <thread>
#include <wiringPi.h>
#define sync delayMicroseconds(5)
#define foreach(e) for (unsigned char e = GPIOController::pin_min; e <= GPIOController::pin_max; e++)
struct GPIOController {
  private:
    constexpr static unsigned int pin_reset = 27;
    constexpr static unsigned int pin_clock = 28;
    constexpr static unsigned int pin_load  = 29;
    constexpr static unsigned int pin_min   = 0;
    constexpr static unsigned int pin_max   = 17;
    constexpr static unsigned char mask[4]  = {0b0001, 0b0010, 0b0100, 0b1000};

    constexpr static std::array<unsigned char, pin_max - pin_min + 1> pin_map = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 21};
    unsigned char phase_A[pin_max - pin_min + 1];
    unsigned char phase_B[pin_max - pin_min + 1];
    unsigned char *phase_read{phase_A};
    unsigned char *phase_write{phase_B};
    std::mutex lock;
    std::thread thread;
    bool should_stop = false;

    void send_reset();
    void send_load();
    void send_clock();
    void send_array();
    void set_low();
    void set_high();
    void flush();
    void gpioloop();
    GPIOController(const GPIOController &c) = delete;
    GPIOController(GPIOController &&c)      = delete;

  public:
    void set(unsigned, int);
    int get(unsigned);
    void swap_buffer();
    void fill_buffer(const pybind11::array_t<int> &input);
    GPIOController();
    ~GPIOController();
};

void GPIOController::send_reset() {
    digitalWrite(pin_reset, LOW);
    sync;
    digitalWrite(pin_reset, HIGH);
    sync;
}
void GPIOController::send_load() {
    digitalWrite(pin_load, LOW);
    sync;
    digitalWrite(pin_load, HIGH);
}
void GPIOController::send_clock() {
    sync;
    digitalWrite(pin_clock, HIGH);
    sync;
    digitalWrite(pin_clock, LOW);
}
void GPIOController::send_array() {
    for (unsigned char i = 0; i < 4; i++) {
        foreach (pin) {
            digitalWrite(pin_map[pin], ((phase_read[pin] & mask[i])) == 0 ? LOW : HIGH);
        }
        send_clock();
    }
}
void GPIOController::set_low() {
    foreach (pin) {
        digitalWrite(pin_map[pin], LOW);
    }
}
void GPIOController::set_high() {
    foreach (pin) {
        digitalWrite(pin_map[pin], HIGH);
    }
}
void GPIOController::flush() {
    send_reset();
    send_array();
    send_load();
    set_low();
}
void GPIOController::gpioloop() {
    while (true) {
        lock.lock();
        if (should_stop) {
            lock.unlock();
            break;
        }
        flush();
        lock.unlock();
        delay(20);
    }
}
void GPIOController::set(unsigned int offset, int value) {
    if (offset < pin_min or offset > pin_max) { throw std::runtime_error("set_phase_buffer: offset out of range!\n"); }
    phase_write[offset] = static_cast<unsigned char>(value);
}
int GPIOController::get(unsigned int offset) {
    if (offset < pin_min or offset > pin_max) { throw std::runtime_error("set_phase_buffer: offset out of range!\n"); }
    return phase_write[offset];
}
void GPIOController::swap_buffer() {
    lock.lock();
    std::swap(phase_read, phase_write);
    lock.unlock();
}
void GPIOController::fill_buffer(const pybind11::array_t<int> &input) {
    pybind11::buffer_info bufi = input.request();
    if (bufi.ndim != 1) { throw std::runtime_error("Not a 1-d array"); }
    if (bufi.shape[0] != GPIOController::pin_max - GPIOController::pin_min + 1) {
        throw std::runtime_error("Size not fit");
    }
    foreach (pin) {
        phase_write[pin] = static_cast<int *>(bufi.ptr)[pin];
    }
}
GPIOController::GPIOController() {
    wiringPiSetup();
    foreach (pin) {
        pinMode(pin_map[pin], OUTPUT);
        phase_read[pin]  = 0;
        phase_write[pin] = 0;
    }
    pinMode(pin_reset, OUTPUT);
    pinMode(pin_clock, OUTPUT);
    pinMode(pin_load, OUTPUT);
    digitalWrite(pin_reset, HIGH);
    digitalWrite(pin_clock, LOW);
    digitalWrite(pin_load, HIGH);
    flush();
    std::thread v(std::bind(&GPIOController::gpioloop, this));
    thread = std::move(v);
    thread.detach();
}
GPIOController::~GPIOController() {
    should_stop = true;
}
PYBIND11_MODULE(libcontroller, m) {
    pybind11::class_<GPIOController>(m, "GPIOController")
        .def(pybind11::init<>())
        .def("set", &GPIOController::set)
        .def("get", &GPIOController::get)
        .def("swap_buffer", &GPIOController::swap_buffer)
        .def("fill_buffer", &GPIOController::fill_buffer);
}