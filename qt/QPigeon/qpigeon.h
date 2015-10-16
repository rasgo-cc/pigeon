#ifndef QPIGEON_H
#define QPIGEON_H

#include <QObject>
#include <QTcpSocket>
#include <QTcpServer>
#include <QJsonDocument>


class QPigeonDataParser : public QObject
{
    Q_OBJECT
public:
    explicit QPigeonDataParser(QObject *parent = 0);


signals:
    void parsed(QByteArray);

public slots:
    virtual void parseData(QByteArray data) = 0;
};

class QPigeonJsonParser : public QPigeonDataParser
{
    Q_OBJECT
public:
    explicit QPigeonJsonParser(QObject *parent = 0);

signals:

public slots:
    void parseData(QByteArray data);

private:
    QString _jsonStr;
    int _depthLevel;
    bool _escChar;
    bool _inString;

};

class QPigeonSerialParser : public QPigeonDataParser
{
    Q_OBJECT
public:
    explicit QPigeonSerialParser(QObject *parent = 0);

signals:

public slots:
    void parseData(QByteArray data);
};

class QPigeonClient : public QTcpSocket
{
    Q_OBJECT
public:
    explicit QPigeonClient(QObject *parent = 0);

    void sendData(const QString &text);

signals:
    void messageReceived(QJsonDocument);

public slots:

private slots:
    void _slotReadyRead();
    void _handleJson(QByteArray jsonData);

private:
    QPigeonJsonParser *_jsonParser;
};

class QPigeonServer : public QObject
{
    Q_OBJECT
public:
    explicit QPigeonServer(QObject *parent = 0);

signals:

public slots:
};

class QPigeonLogger : public QObject
{
    Q_OBJECT
public:
    explicit QPigeonLogger(QObject *parent = 0);

signals:

public slots:
};


#endif // QPIGEON_H
