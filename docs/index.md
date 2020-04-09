# What is Peering Manager?

Peering Manager is an open source web application designed to help manager and
document peering networks and peering sessions. It is not a tool that aims to
replace the great [PeeringDB](https://peeringdb.com).

# Application Stack

Peering Manager is built on the [Django](https://djangoproject.com/) Python
framework. It runs as a WSGI service behind your choice of HTTP server.

| Function     | Component             |
|--------------|-----------------------|
| HTTP Service | Apache 2 or nginx     |
| WSGI Service | gunicorn or uWSGI     |
| Application  | Django/Python         |
| Database     | PostgreSQL            |

# Getting Started

See the [setup guide](setup/1-postgresql.md) for help getting Peering Manager
up and running.

# Helping

You can help this project in many ways. Of course you can ask for features,
give some ideas for future development, open issues if you found any and
contribute to the code with pull requests and patches.

You can also support the development of this project by
[donating some money](https://paypal.me/GuillaumeMazoyer). Developing such
project can be time consuming and it is done on personal time. Giving few
dollars/euros/pounds/etc... can be a way to say thanks and help to free some
time to develop this project.

# Spreading The Word

  * [RIPE76 Peering Manager - Easing Peering Sessions Management](https://ripe76.ripe.net/archives/video/13/) by Guillaume Mazoyer (English)
  * [FRnOG32 Peering Automation and Documentation](https://www.dailymotion.com/video/x756n1e?playlist=x6c4hk) by Guillaume Mazoyer (French)
  * [LUNOG2 A better Internet thanks to peering and automation](https://drive.mazoyer.eu/index.php/s/3RiyrPQd3Tdwc96) by Guillaume Mazoyer (English)
