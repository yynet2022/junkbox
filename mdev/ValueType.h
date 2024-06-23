// -*- c++ -*-
#ifndef _VALUE_TYPE__H
#define _VALUE_TYPE__H

typedef long long int size_type;

// 0: double
// 1: long double
// 2: dd_real
// 3: qd_real
// 4: __float128
#define VALUE_TYPE 0

#if VALUE_TYPE == 0
typedef double value_type;

#elif VALUE_TYPE == 1
typedef long double value_type;

#elif VALUE_TYPE == 2
#include "qd/dd_real.h"
typedef dd_real value_type;

#elif VALUE_TYPE == 3
#include "qd/qd_real.h"
typedef qd_real value_type;

#elif VALUE_TYPE == 4
#include <quadmath.h>
typedef __float128 value_type;

#include <iostream>
#include <iomanip>
namespace std {
  inline value_type log (const value_type &v) { return logq (v); }
  inline value_type sqrt (const value_type &v) { return sqrtq (v); }
  inline value_type exp (const value_type &v) { return expq (v); }
  inline value_type abs (const value_type &v) { return (v < 0.0) ? -v : v; }

  inline ostream&
  operator<< (ostream &s, const value_type &v) {
    char buf [128];
    quadmath_snprintf (buf, sizeof buf, "%.18Qe", v);
    return s << buf;
  }
  inline istream&
  operator>> (istream &s, value_type &v) {
    abort ();
    return s;
  }
}

#else
#error "error: unknown value_type"

#endif

#endif // ! _VALUE_TYPE__H
