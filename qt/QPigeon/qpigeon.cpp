#include "qpigeon.h"

QPigeonClient::QPigeonClient(QObject *parent) : QObject(parent)
{
    connect(&_skt, SIGNAL(readyRead()),
            this, SLOT(_slotReadyRead()));
}

void QPigeonClient::connectToServer(const QString &address, int port)
{
    QHostAddress host;
    if(address.toLower() == "localhost")
    {
        host = QHostAddress(QHostAddress::LocalHost);
    }
    else
    {
        host = QHostAddress(address);
    }
    _skt.connectToHost(host, port);
}

void QPigeonClient::disconnectFromServer()
{
    _skt.disconnectFromHost();
}

void QPigeonClient::sendData(const QString &text)
{
    if(_skt.isWritable())
        _skt.write(text.toLatin1());
}

void QPigeonClient::_slotReadyRead()
{

}

void QPigeonClient::_handleJson(QJsonDocument doc)
{

}
