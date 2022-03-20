all: build run

build:
	go build github.com/erazemk/flati

clean:
	rm flati

run:
	./flati

.PHONY: all clean run