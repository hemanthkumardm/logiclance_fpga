CC = gcc
CFLAGS = -Wall

all: build

build: main.c
	@$(CC) $(CFLAGS) -o adder_model main.c

run: build
	./adder_model

manual: build
	@./adder_model

clean:
	rm -f adder_model
