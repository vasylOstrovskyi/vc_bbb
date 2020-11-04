# vc_bbb

BigBlueButton videoconferencing plugin for Indico.

Meanwhile, only basic functions are available. Check for updates or modify the code yourself to suit your needs.

To install and configure:

1. Install and configure BigBlueButton (https://bigbluebutton.org/)

2. Get plugin source
git clone https://github.com/vasylOstrovskyi/vc_bbb.git

3. Switch to indico user and activate evironment
su - indico
source ~/.venv/bin/activate

4. Compile and install plugin
cd vc_bbb
python setup.py install
cd

5. Enable plugin in the config file. In indico.conf, add or modify line
PLUGINS={'vc_bbb'}
(append 'vc_bbb' to the list if you have some plugins installed)

6. Restart indico
touch ~/web/indico.wsgi

7. Open indico in your browser, and go to Administration->Plugins, click on BigBlueButton

8. On your BigBlueButton server, issue
bbb-conf --secret
and copy values for URL and secret to the corresponding fields, click Save.

9. Use it and report bugs.

How to use it.

On the event setup page, select Services->Videoconference.
Here you can create and configure rooms for event, pre-upload presentations, set moderators etc.

If the moderator visits the event page, they can start meeting anytime before the scheduled end of the meeting. If the meeting was terminated due to any reason, it can be restarted ans many times as necessary.

If any other user visits the event page, and if the meeting is running, they can join it (if the user is not logeed in, they will be asked to login first to identify themselves)

After meeting end, recordings (if the moderator choose to record session) are available as soon as they are processed by the BigBlueButton server (it may take from several minutes to several hours)
Recordings which are not needed, can be removed on the event setup page.
