#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    if (argc != 3) {
        fprintf(stderr, "usage: concat number output_file\n");
        exit(1);
    }

    int number = atoi(argv[1]);

    FILE *fp1, *fp2;
    fp1 = fopen(argv[2], "a");
    if (fp1 == NULL) {
        fprintf(stderr, "Unable to open the file %s\n", argv[2]);
        exit(1);
    }

    char buffer1[1024];
    char buffer2[10240];

    for (int i = 1; i <= number; i++) {
        sprintf(buffer1, "%d.fit", i);
        fp2 = fopen(buffer1, "r");
        if (fp2 == NULL) {
            fprintf(stderr, "Unable to open the file %s\n", buffer1);
            exit(1);
        }
        char *string;
        while ((string = fgets(buffer2, 10240, fp2)) != NULL) {
            fputs(string, fp1);
        }
        fclose(fp2);
    }
    fclose(fp1);
    exit(0);
}


