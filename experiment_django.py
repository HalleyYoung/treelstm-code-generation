import subprocess


if __name__ == '__main__':
    # with unary closures
    # subprocess.run("python main.py -dataset django -cuda -encoder bi-lstm-dropout "
    #                "-output_dir ./results/django/unary_closures/bilstm "
    #                "-batch_size 50 "
    #                "-unary_closures "
    #                "-data_dir ./preprocessed/django", shell=True)

    subprocess.run("python main.py -dataset django -cuda -syntax dependency "
                   "-output_dir ./results/django/unary_closures/dependency "
                   "-batch_size 50 "
                   "-unary_closures "
                   "-data_dir ./preprocessed/django", shell=True)

    subprocess.run("python main.py -dataset django -cuda -syntax pcfg "
                   "-output_dir ./results/django/unary_closures/pcfg "
                   "-batch_size 50 "
                   "-unary_closures "
                   "-data_dir ./preprocessed/django", shell=True)

    subprocess.run("python main.py -dataset django -cuda -syntax ccg "
                   "-output_dir ./results/django/unary_closures/ccg "
                   "-batch_size 50 "
                   "-unary_closures "
                   "-data_dir ./preprocessed/django", shell=True)

    # without unary closures
    subprocess.run("python main.py -dataset django -cuda -encoder bi-lstm-dropout "
                   "-output_dir ./results/django/no_unary_closures/bilstm "
                   "-batch_size 50 "
                   "-no_unary_closures "
                   "-data_dir ./preprocessed/django", shell=True)

    subprocess.run("python main.py -dataset django -cuda -syntax dependency "
                   "-output_dir ./results/django/no_unary_closures/dependency "
                   "-batch_size 50 "
                   "-no_unary_closures "
                   "-data_dir ./preprocessed/django", shell=True)

    subprocess.run("python main.py -dataset django -cuda -syntax pcfg "
                   "-output_dir ./results/django/no_unary_closures/pcfg "
                   "-batch_size 50 "
                   "-no_unary_closures "
                   "-data_dir ./preprocessed/django", shell=True)

    subprocess.run("python main.py -dataset django -cuda -syntax ccg "
                   "-output_dir ./results/django/no_unary_closures/ccg "
                   "-batch_size 50 "
                   "-no_unary_closures "
                   "-data_dir ./preprocessed/django", shell=True)