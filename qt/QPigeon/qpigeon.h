#ifndef QPIGEON_H
#define QPIGEON_H

#include <QObject>
#include <QTcpSocket>
#include <QTcpServer>

class QPigeonClient : public QObject
{
    Q_OBJECT
public:
    explicit QPigeonClient(QObject *parent = 0);

    void connectToServer(const QString &address, int port);
    void disconnectFromServer();
    void sendData(const QString &text);

signals:
    void messageReceived(QJsonDocument);

public slots:

private slots:
    void _slotReadyRead();
    void _handleJson(QJsonDocument doc);

private:
    QTcpSocket _skt;
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

class QPigeonDataParser : public QObject
{
    Q_OBJECT
public:
    explicit QPigeonDataParser(QObject *parent = 0);

signals:

public slots:
};

class QPigeonJsonParser : public QObject
{
    Q_OBJECT
public:
    explicit QPigeonJsonParser(QObject *parent = 0);

signals:

public slots:
};

class QPigeonSerialParser : public QObject
{
    Q_OBJECT
public:
    explicit QPigeonSerialParser(QObject *parent = 0);

signals:

public slots:
};


#endif // QPIGEON_H
