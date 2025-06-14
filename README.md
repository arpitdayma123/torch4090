# torch4090


##Dockerfile-4090  有下载链接之后，在Dockerfile 43行后添加以下命令


RUN   wget -P / <download_url>    ##代替换换下载链接   
RUN dpkg -i /cudnn-local-repo-ubuntu2204-8.6.0.163_1.0-1_amd64.deb

RUN cp /var/cudnn-local-repo-ubuntu2204-8.6.0.163/cudnn-local-FAED14DD-keyring.gpg /usr/share/keyrings/

RUN  cd /var/cudnn-local-repo-ubuntu2204-8.6.0.163/ && dpkg -i libcudnn8_8.6.0.163-1+cuda11.8_amd64.deb libcudnn8-dev_8.6.0.163-1+cuda11.8_amd64.deb libcudnn8-samples_8.6.0.163-1+cuda11.8_amd64.deb




###需要额外下载的requirement包，已添加
echo "requests" >>  requirements_0.txt && echo "diffusers" >>  requirements_0.txt 
