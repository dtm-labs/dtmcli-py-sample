### 快速开始

#### 启动dtm

首先安装docker版本18以上

```
git clone https://github.com/yedf/dtm
cd dtm
docker-compose up
```

#### 运行示例
运行服务
```
flask run
```
触发事务
```
curl localhost:5000/api/fireTcc
```