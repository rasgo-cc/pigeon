#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QJsonDocument>
#include "qpigeon.h"

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = 0);
    ~MainWindow();

private slots:
    void _slotConnect();
    void _slotSend();
    void _slotMessage(QJsonDocument doc);

private slots:
    void updateInterface();

private:

    Ui::MainWindow *ui;
    QPigeonClient _client;
};

#endif // MAINWINDOW_H
