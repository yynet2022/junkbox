// -*- c++ -*-
#ifndef NEWTON_IF_H_
#define NEWTON_IF_H_

#include "ValueType.h"

class NewtonIF {
 public:
  NewtonIF () {}
  virtual ~NewtonIF () {}

  virtual void setup() = 0;
  virtual void solve() = 0;
  virtual void update() = 0;
  virtual bool isConverge() = 0;
  virtual void setVolt(const value_type &volt) = 0;
};

#endif // NEWTON_IF_H_
