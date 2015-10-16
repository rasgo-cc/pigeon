#include "qpigeon.h"

#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonValue>
#include <QJsonParseError>

QPigeonDataParser::QPigeonDataParser(QObject *parent) :
    QObject(parent)
{

}

QPigeonSerialParser::QPigeonSerialParser(QObject *parent) :
    QPigeonDataParser(parent)
{

}

void QPigeonSerialParser::parseData(QByteArray data)
{

}

QPigeonJsonParser::QPigeonJsonParser(QObject *parent) :
    QPigeonDataParser(parent)
{
    _inString = false;
    _escChar = false;
    _depthLevel = 0;
    _jsonStr = "";
}

void QPigeonJsonParser::parseData(QByteArray data)
{
    bool done = false;
    char *p_data = data.data();
    for(int i = 0; i < data.count(); i++)
    {
        if(*p_data == '\"')
        {
            if(!_inString)
                _inString = true;
            else
            {
                if(!_escChar)
                    _inString = false;
                else
                    _escChar = false;
            }
        }

        if(_inString)
        {
            if(*p_data == '\\')
                _escChar = true;
        }
        else
        {
            if(*p_data == '{')
            {
                if(_depthLevel == 0)
                    _jsonStr = "";
                _depthLevel++;
            }
            else if(*p_data == '}')
            {
                _depthLevel--;
                if(_depthLevel == 0)
                    done = true;
            }
        }
        _jsonStr += *p_data++;

        if(done)
        {
            QJsonParseError jsonError;
            QJsonDocument jsonDoc = QJsonDocument::fromJson(_jsonStr.toLatin1(), &jsonError);
            if(jsonError.error != QJsonParseError::NoError)
            {
                qDebug() << jsonError.errorString();
            }
            else
            {
                emit parsed(jsonDoc.toJson(QJsonDocument::Compact));
                done = false;
            }
        }

    }
}


QPigeonClient::QPigeonClient(QObject *parent) : QTcpSocket(parent)
{
    _jsonParser = new QPigeonJsonParser(this);

    connect(_jsonParser, SIGNAL(parsed(QByteArray)),
            this, SLOT(_handleJson(QByteArray)));

    connect(this, SIGNAL(readyRead()),
            this, SLOT(_slotReadyRead()));
}

void QPigeonClient::sendData(const QString &text)
{
    if(isWritable())
        write(text.toLatin1() + "\r\n");
}

void QPigeonClient::_handleJson(QByteArray jsonData)
{
    QJsonDocument doc = QJsonDocument::fromJson(jsonData);

    QStringList obj_keys = doc.object().keys();
    if(obj_keys.contains("message"))
    {
        emit messageReceived(doc);
    }
    else
    {
        qFatal("Unknown JSON format");
        return;
    }
}


void QPigeonClient::_slotReadyRead()
{
    _jsonParser->parseData(readAll());
}



