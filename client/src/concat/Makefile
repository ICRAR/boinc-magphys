
.c.o:
	gcc -std=c99 -c -o $@ $<

concat_x86_64-pc-linux-gnu: concat.c
	gcc -g -O2 -m64 -o $@ $^

concat_i686-pc-linux-gnu: concat.c
	gcc -g -O2 -m32 -o $@ $^

concat_x86_64-apple-darwin: concat.c
	gcc -g -O2 -o $@ $^
