文件清单
------------------------------------
1 my-realtime-chart 
    UI version 1.0 
    实时显示随机数
2 vue_project2 
    UI version 1.5
    正弦波实时显示
3 vue_project3
    UI version 2.0
    新增总览图
    新增主图滚轮缩放与左键拖动功能
    新增数据拟合功能
4 vue_project4
    UI version 3.0（开发中）
    新增暂停与继续接收功能
    后端新增外部接口
    以及其他后续功能
5 data_send.py
    UI 3.0配套程序，用于测试后端的外部接口，负责向web_server2传输数据
6 Fit.py
    之前的数据拟合程序，用于参考
7 fit_service.py
    UI 2.0/3.0配套程序，用于数据拟合
8 vue_sin_server1.py
    UI 1.5后端程序
9 web_server2.py
    UI 3.0后端程序
10 websocket_server.py
    UI 2.0后端程序

使用说明
------------------------------------
UI 2.0使用说明
用powershell打开wuchengyu文件夹
执行python websocket_server.py以及python fit_service.py
用powershell打开vue_project3文件夹
执行npm run dev
ctrl + 左键 点击网址