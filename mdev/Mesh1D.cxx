//
// Copyright (C) 2024 YYNET.
// This file is part of mdev.
//
#include "Mesh1D.h"
#include "MaterialInfo.h"
#include "ValueType.h"

#include <cassert>
using namespace std;

Mesh1D::Mesh1D (const vector<Recipe> &rcps,
		const vector<const MaterialInfo *> &minfo,
		const value_type &start): __nN(0)
{
  vector<Recipe>::const_iterator rcp, rend = rcps.end();
  for (rcp = rcps.begin(); rcp != rend; rcp ++)
    __nN += rcp->ndiv;
  __nN += 1;

  __cN.resize (__nN);
  __iLR.resize (__nN - 1);

  vector<value_type>::iterator c = __cN.begin ();
  vector<int>::iterator r = __iLR.begin ();
  value_type p = start;
  int iR = 0;
  for (rcp = rcps.begin (); rcp != rend; ++rcp, ++iR) {
    const value_type d = rcp->length / rcp->ndiv;
    for (int i = 0; i < rcp->ndiv; i ++, p += d) {
      *c++ = p;
      *r++ = iR;
    }
  }
  *c = p;

  __iNR.resize (__nN);
  for (int iN = 0; iN < __nN; iN ++) {
    // const MaterialInfo *m = 0;
    int priority = 0x0fffffff;
    int iR = -1;
    for (int i = 0; i < nNL(iN); i ++) {
      const int iL = iNL (iN, i);
      const MaterialInfo *mm = minfo [iLR(iL)];
      const int p = mm->priority ();
      if (p < priority) {
	priority = p;
	iR = iLR (iL);
      }
    }
    assert (iR >= 0);
    __iNR [iN] = iR;
  }
}
