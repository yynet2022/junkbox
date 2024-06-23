// -*- c++ -*-
#ifndef _MATRIX__H
#define _MATRIX__H

#include "ValueType.h"
#include <vector>
#include <cstdlib>
#include <cmath>
#include <cassert>

class Mesh1D;

class Matrix {
public:
  typedef long long int size_type;
  typedef ::value_type value_type;

private:
  size_type __n, __nmz;
  std::vector<size_type> __hdr, __jcol, __lpt, __block, __btop;
  std::vector<value_type> __a, __x, __b, __lval, __uval;

  int uranus();
  int cronos();

  void __setup(const Mesh1D &mesh);

public:
  Matrix (const Mesh1D &mesh, const std::vector<size_type> &block);
  // Matrix (const Mesh1D &mesh);
  Matrix(const char *Ammf);

  value_type& A(const size_type &i, const size_type &j) {
    assert(0 <= i && i < __n);
    assert(0 <= j && j < __n);
    for (size_type ii = __hdr[i]; ii < __hdr[i + 1]; ii ++)
      if (__jcol[ii] == j)
        return __a[ii];
    std::abort();
  }
  value_type& A(const size_type &I, const size_type &J,
                const size_type &i, const size_type &j) {
    assert(i < __block[I] && j < __block[J]);
    const size_type II = __btop [I] + i;
    for (size_type ii = __hdr[II]; ii < __hdr[II+1]; ii ++)
      if (__jcol[ii] == __btop[J]+j)
        return __a[ii];
    std::abort();
  }
  void clear() {
    fill(__a.begin(), __a.end(), value_type(0));
    fill(__x.begin(), __x.end(), value_type(0));
    fill(__b.begin(), __b.end(), value_type(0));
    fill(__lval.begin(), __lval.end(), value_type(0));
    fill(__uval.begin(), __uval.end(), value_type(0));
  }

  const std::vector<size_type> &hdr() const { return __hdr; }
  const std::vector<size_type> &jcol() const { return __jcol; }
  const std::vector<size_type> &block() const { return __block; }
  const std::vector<size_type> &btop() const { return __btop; }
  const std::vector<value_type> &a() const { return __a; }
  std::vector<value_type> &a() { return __a; }

  const value_type &x(const size_type &I, const size_type &i = 0) const {
    assert(i < __block[I]);
    return __x[__btop[I] + i];
  }
  value_type &x(const size_type &I, const size_type &i = 0) {
    assert(i < __block[I]);
    return __x[__btop[I] + i];
  }
  value_type x2norm() const {
    value_type xx = value_type(0);
    for (size_type i = 0; i < __n; i ++)
      xx += __x[i] * __x[i];
    return sqrt(xx);
  }

  const value_type &b(const size_type &I, const size_type &i = 0) const {
    assert(i < __block[I]);
    return __b[__btop[I] + i];
  }
  value_type &b(const size_type &I, const size_type &i = 0) {
    assert(i < __block[I]);
    return __b[__btop[I] + i];
  }
  value_type b2norm() const {
    value_type bb = value_type(0);
    for (size_type i = 0; i < __n; i ++)
      bb += __b[i] * __b[i];
    return sqrt(bb);
  }

  value_type r2norm() const {
    value_type rr = value_type(0);
    for (size_type i = 0; i < __n; i ++) {
      value_type r = __b[i];
      for (size_type ii = __hdr[i]; ii < __hdr[i+1]; ii ++)
        r -= __a[ii] * __x[__jcol[ii]];
      rr += r * r;
    }
    return sqrt(rr);
  }

  void solve(bool display = false);
};

#endif // ! _MATRIX__H
