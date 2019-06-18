from tkinter import *
from tkinter import messagebox
from openpty import *

window = Tk()
window.title("XTS TEST")
window.geometry("500x600")

passwd = "cvte"

# 环境准备
#test_env_label = Label(window, text="input env prepare", bg="blue", fg="white", font=("Arial", 12), width=30, height=2)
#test_env_label.pack()
#test_env_text = Text(window, width=35, height=5)
#test_env_text.pack()

# 测试类型
test_type_label = Label(window, text="choose test type", bg="blue", fg="white", font=("Arial", 12), width=30, height=2)
test_type_label.pack()
test_type_var = IntVar()
test_type = [('cts', 1), ('vts', 2), ("gts", 3), ("cts-on-gsi", 4)]


def change_type():
    num = test_type_var.get()
    if num in [1, 2, 3, 4]:
        messagebox.showinfo(title="info", message="you choose test type is " + test_type[num-1][0])


for t_type, num in test_type:
    test_type_radio = Radiobutton(window, text=t_type, value=num, variable=test_type_var)
    test_type_radio.pack()

# 创建选择的测试范围，是全部运行还是运行单个testcase，或者只运行几个module，或只排除几个module
test_range_label = Label(window, text="choose test range", bg="blue", fg="white", font=("Arial", 12), width=30, height=2)
test_range_label.pack()
test_range_var = IntVar()
test_range = [('all   testcase', 1), ('one testcase', 2), ("include filter", 3), ("exclude filter", 4)]


def change():
    num = test_range_var.get()
    if num in [1, 2, 3, 4]:
        messagebox.showinfo(title="info", message="you choose test range is " + test_range[num-1][0])


for t_range, num in test_range:
    test_range_radio = Radiobutton(window, text=t_range, value=num, variable=test_range_var)
    test_range_radio.pack()

test_module_label = Label(window, text="input test module", bg="blue", fg="white", font=("Arial", 12), width=30, height=2)
test_module_label.pack()
test_module_var = StringVar()
test_module_input = Entry(window, show=None, textvariable=test_module_var, font=("Arial", 12), width=30)
test_module_input.pack()

test_num_label = Label(window, text="input after failed test number", bg="blue", fg="white", font=("Arial", 12), width=30, height=2)
test_num_label.pack()
test_num_var = IntVar()
test_num_input = Entry(window, show=None, textvariable=test_num_var, font=("Arial", 12), width=30)
test_num_input.pack()


def run_test():
    
    test_type_dict = {1: "cts", 2: "vts", 3: "gts", 0: "cts", 4: "cts-on-gsi"}
    run_type = test_type_dict[test_type_var.get()]
    if run_type == "cts":
        run_type_dir = "android-cts"
        try:
            subprocess.check_call('./cts_env.sh')
        except subprocess.SubprocessError as e:
            print(e.returncode)
            print(e.cmd)
            print(e.output)
    elif run_type == "vts" or run_type == "cts-on-gsi":
        run_type_dir = "android-vts"
    else:
        try:
            subprocess.check_call('./gts_env.sh')
        except subprocess.SubprocessError as e:
            print(e.returncode)
            print(e.cmd)
            print(e.output)
        run_type_dir = "android-gts"
    run_range = test_range_var.get()
    test_module = test_module_input.get()
    test_num_in = test_num_input.get()
    if test_num_in in ['0', '']:
        test_num = 3
    else:
        test_num = int(test_num_in)

    # 不传参数时，使用默认值处理

    old = tty.tcgetattr(0)
    # 备份报告文件夹然后清除
    try:
        subprocess.check_call(['./clean_dir.sh', passwd, run_type_dir])
    except subprocess.SubprocessError as e:
        print(e.returncode)
        print(e.cmd)
        print(e.output)
    thread_adb = adb_shell()
    thread_xts = cts_tf(run_type, test_module, run_range, test_num)
    thread_adb.setDaemon(True)
    thread_xts.setDaemon(True)
    thread_adb.start()
    thread_xts.start()
    try:
        while True:
            if not thread_adb.is_alive() or not thread_xts.is_alive():
                break
    except (KeyboardInterrupt):
        print("enter key interrupt")
        thread_adb.stop()
        thread_xts.stop()
    tty.tcsetattr(0, tty.TCSAFLUSH, old)
    exit(0)


commit_button = Button(window, text='请点击开始测试', width=30, command=run_test)
commit_button.pack()
window.mainloop()







