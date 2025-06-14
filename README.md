# torch4090


##Dockerfile

RUN dpkg -i /cudnn-local-repo-ubuntu2204-8.6.0.163_1.0-1_amd64.deb

RUN cp /var/cudnn-local-repo-ubuntu2204-8.6.0.163/cudnn-local-FAED14DD-keyring.gpg /usr/share/keyrings/

RUN  cd /var/cudnn-local-repo-ubuntu2204-8.6.0.163/ && dpkg -i libcudnn8_8.6.0.163-1+cuda11.8_amd64.deb libcudnn8-dev_8.6.0.163-1+cuda11.8_amd64.deb libcudnn8-samples_8.6.0.163-1+cuda11.8_amd64.deb

