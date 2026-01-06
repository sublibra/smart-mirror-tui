#/bin/bash

# Install dependencies
sudo apt install cage foot fontconfig wlr-randr -y

# Configure foot
cp ./foot.ini ~/.config/foot/foot.ini

# Download nerdfonts
mkdir /.local/share/fonts
cd ~/.local/share/fonts
wget https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.tar.xz
tar -xvf JetBrainsMono.tar.xz

# Install fontconfig and update font list
sudo apt install fontconfig -y
fc-cache -fv

# Add video access to the user to allow use of screen
sudo usermod -aG tty,video,input,render $USER

# Remove the pointer
mkdir -p ~/.icons/default/cursors
mv left_ptr ~/.icons/default/cursors/left_ptr
echo -e "[Icon Theme]\nName=default\nInherits=default" > ~/.icons/default/index.theme

# Install service
cp smart-mirror.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable smart-mirror.service

