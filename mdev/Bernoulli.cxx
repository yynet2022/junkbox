//
// Copyright (C) 2024 YYNET.
// This file is part of mdev.
//
#include "Bernoulli.h"
#include "ValueType.h"

#if VALUE_TYPE == 0
# include "qd/dd_real.h"
#endif

#include <cmath>
using namespace std;

// B(x) = x / (exp(x) - 1)
template <typename T>
inline T
_B (const T &x)
{
  if (x == T (0))
    return T (1.0);
  return x / (exp (x) - 1);
}

// exp(x) - 1
template <typename T>
inline T
_UD (const T &x)
{
  return exp (x) - 1;
}

// dB(x) / dx
template <typename T>
inline T
_BdB (const T &x)
{
  if (x == value_type (0))
    return value_type (-0.5);
  return (1 - _B(x) * exp (x)) / _UD (x);
}

#if VALUE_TYPE == 0
value_type
Bernoulli::B (const value_type &x) { return _B<dd_real>(x).x[0]; }

value_type
Bernoulli::UD (const value_type &x) { return _UD<dd_real>(x).x[0]; }

value_type
Bernoulli::BdB (const value_type &x) { return _BdB<dd_real>(x).x[0]; }

#else

value_type
Bernoulli::B (const value_type &x) { return _B<value_type>(x); }

value_type
Bernoulli::UD (const value_type &x) { return _UD<value_type>(x); }

value_type
Bernoulli::BdB (const value_type &x) { return _BdB<value_type>(x); }

#endif
