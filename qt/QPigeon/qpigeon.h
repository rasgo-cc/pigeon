#ifndef QPIGEON_H
#define QPIGEON_H

#include <QObject>

class QPigeon : public QObject
{
    Q_OBJECT
public:
    explicit QPigeon(QObject *parent = 0);

signals:

public slots:
};

#endif // QPIGEON_H
