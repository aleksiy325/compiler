CC=clang
IR=test.ir

run:
	llc -filetype=obj $(IR)
	$(CC) $(IR).o -o output
	./output

default: 
	python3 compile.py
	run

clean:
	rm $(IR)
	rm $(IR).o
	rm output
	rm tmp

test: 
	python3 -m pytest --cov=lang
	python3 -m coverage html