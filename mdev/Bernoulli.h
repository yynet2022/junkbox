// -*- c++ -*-
// Copyright (C) 2024 YYNET.
// This file is part of mdev.
//
#ifndef BERNOULLI_H_
#define BERNOULLI_H_

#include "ValueType.h"

class Bernoulli {
public:
  // B(x) = x / (exp (x) - 1)
  static value_type B (const value_type &x);

  // dB(x)/dx
  static value_type BdB (const value_type &x);

  // std::exp(x) - 1
  static value_type UD (const value_type &x);
};


#endif  // ! BERNOULLI_H_
