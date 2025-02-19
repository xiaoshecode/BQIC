PYTHON API说明文档

一、代码概述

men_gen这段代码定义了多个类，用于处理DDS数据、AWG的幅度、相位和频率数据以及 TTL数据。代码自动化将这些生成的二进制数据写入文件。最后提供了一些处理DDS、AWG、TTL数据的简单例程。

二、类说明

**1. DDSArrayHandler 类**

功能：用于生成 128 位（DDS标识符、频率、相位、幅度）和 32 位（时间）的 DDS 数据数组。可进行多频DDS处理。

**2. AWG_AMP_array_handler 类**

功能：处理 AWG 幅度数据的 128 位和 32 位数组。

**3. AWG_PHASE_array_handler 类**

功能：处理 AWG 相位数据的 128 位和 32 位数组。

方法：与 AWG_AMP_array_handler 类类似，针对相位数据进行处理。

**4. AWG_FREQ_array_handler 类**

功能：处理 AWG 频率数据的 128 位和 32 位数组。

方法：与 AWG_AMP_array_handler 类类似，针对频率数据进行处理。

**5. TTL_handler 类**

功能：处理 TTL 数据的 16 位和 32 位数组。

三、文件生成函数

**1. write_awg_array_to_file 函数**

功能：

将 AWG_AMP_handler_array、AWG_PHASE_handler_array 和 AWG_FREQ_handler_array 中的 128 位和 32 位数据数组写入两个文件。

参数介绍：

FILE1：用于写入 128 位数据的文件路径。

FILE2：用于写入 32 位数据的文件路径。

AWG_AMP_handler_array：包含 AWG_AMP_array_handler 实例的列表。

AWG_PHASE_handler_array：包含 AWG_PHASE_array_handler 实例的列表。

AWG_FREQ_handler_array：包含 AWG_FREQ_array_handler 实例的列表。

**2. write_ttl_array_to_file 函数**

功能：

将 TTL_handler 类中存储的 16 位和 32 位数据数组写入两个文件。

参数介绍：

file1：用于写入 16 位数据的文件路径。

file2：用于写入 32 位数据的文件路径。

param：包含 TTL_handler 实例的列表。

**3. write_dds_array_to_file 函数**

功能：

将 DDSArrayHandler 类中存储的 128 位和 32 位数据数组写入两个文件。

参数：

file1：用于写入 128 位数据的文件路径。

file2：用于写入 32 位数据的文件路径。

param：包含 DDSArrayHandler 实例的列表。

四、文件合并函数

**1. merge_files_with_header 函数**

功能：

合并两个文件，并在新文件的第一行写入指定格式的标头行，标头行包含两个文件行数之和的 16 进制编码。

参数：

file1：第一个文件的路径。

file2：第二个文件的路径。

output_file：输出文件的路径。

**2. merge_param_files_with_header 函数**

功能：

为单个文件添加特定格式的标头行，标头行包含文件行数的 16 进制编码。

参数：

file1：要添加标头的文件路径。

output_file：输出文件的路径。
