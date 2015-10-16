#include "mainwindow.h"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);

    connect(&_client, SIGNAL(stateChanged(QAbstractSocket::SocketState)),
            this, SLOT(updateInterface()));
    connect(&_client, SIGNAL(messageReceived(QJsonDocument)),
            this, SLOT(_slotMessage(QJsonDocument)));

    connect(ui->buttonConnect, SIGNAL(clicked(bool)),
            this, SLOT(_slotConnect()));

    connect(ui->buttonSend, SIGNAL(clicked(bool)),
            this, SLOT(_slotSend()));
    connect(ui->lineData, SIGNAL(returnPressed()),
            this, SLOT(_slotSend()));

}

MainWindow::~MainWindow()
{
    delete ui;
}

void MainWindow::_slotConnect()
{
    bool connected = _client.state() == QPigeonClient::ConnectedState;
    if(!connected)
    {
        QString addrStr = ui->lineHost->text();
        QHostAddress hostAddr;
        if(addrStr == "localhost")
        {
            hostAddr = QHostAddress(QHostAddress::LocalHost);
        }
        else
        {
            hostAddr = QHostAddress(addrStr);
        }
        _client.connectToHost(hostAddr, ui->spinPort->value());
    }
    else
    {
        _client.disconnectFromHost();
    }
}

void MainWindow::_slotSend()
{
    _client.sendData(ui->lineData->text());
    ui->lineData->clear();
}

void MainWindow::_slotMessage(QJsonDocument doc)
{
    ui->textLog->append(doc.toJson(QJsonDocument::Compact));
}

void MainWindow::updateInterface()
{
    bool connected = _client.state() == QPigeonClient::ConnectedState;

    ui->lineHost->setEnabled(!connected);
    ui->spinPort->setEnabled(!connected);

    if(!connected)
        ui->buttonConnect->setText("Connect");
    else
        ui->buttonConnect->setText("Disconnect");
}
