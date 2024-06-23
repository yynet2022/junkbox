// -*- c++ -*-
#ifndef _MESH_1D__H
#define _MESH_1D__H

#include "ValueType.h"
#include <vector>
#include <string>
#include <cmath>
#include <cassert>
#include <cstdlib>

class MaterialInfo;

struct Recipe {
  std::string material;
  value_type length;
  int ndiv;
  value_type donor, acceptor;

  Recipe (): material (), length (), ndiv (), donor (), acceptor () {}
  Recipe (const std::string &mat,
	  value_type len, int n, value_type d, value_type a)
    : material (mat), length (len), ndiv (n), donor (d), acceptor (a) {}
};

class Mesh1D {
private:
  int __nN;
  std::vector<value_type> __cN;
  std::vector<int> __iNR, __iLR;

public:
  Mesh1D (const std::vector<Recipe> &rcps,
	  const std::vector<const MaterialInfo *> &minfo,
	  const value_type &start = 0.0);
  ~Mesh1D () {}

  int dim () const { return 1; }

  int nN () const { return __nN; }
  const value_type *cN (int i) const { return & __cN [i]; }
  int iNR (int i) const { return __iNR [i]; }

  int nL () const { return __nN - 1; }
  int nLN (int iL) const { return 2; }
  int iLN (int iL, int j) const { return iL + j; }
  int iLR (int iL) const { return __iLR [iL]; }

  value_type vL (int iL) const { return (__cN [iL + 1] - __cN [iL]) * 1e-4L; }
  value_type vF (int iL) const { return 1e-8L; }

  int nNL (int iN) const { return (iN == 0 || iN == nN() - 1) ? 1 : 2; }
  int iNL (int iN, int j) const {
    assert(0 <= iN && iN < nN());
    assert(0 <= j && j < nNL(iN));
    return std::max (0, iN + j - 1); }
  value_type vCV (int iN, int i) const {
    const int iL = iNL (iN, i);
    return vF (iL) * vL (iL) * 0.5L;
  }
  value_type vCV (int iN) const {
    value_type cv = 0.0L;
    for (int i = 0; i < nNL (iN); i ++)
      cv += vCV (iN, i);
    return cv;
  }
};

#endif // ! _MESH_1D__H
