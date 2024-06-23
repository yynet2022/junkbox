//
// Copyright (C) 2024 YYNET.
// This file is part of mdev.
//
#include "Matrix.h"
#include "Mesh1D.h"

#include <iostream>
#include <vector>
#include <list>
#include <fstream>
#include <sstream>
#include <string>
#include <cstdlib>
#include <cassert>
using namespace std;

Matrix::Matrix(const Mesh1D &mesh,
               const vector<size_type> &block)
{
  assert(size_t(mesh.nN()) == block.size());
  __block = block;
  __setup(mesh);
}

Matrix::Matrix(const char *Ammf)
{
  ifstream ifs(Ammf);
  if (!ifs) {
    cerr << "Cannot open file: " << Ammf << endl;
    abort();
  }

  string line;
  size_type n = 0, m = 0, nmz = 0, k = 0;

  vector<size_type> irow, jcol;
  vector<value_type> aval;
  while (ifs.good()) {
    getline(ifs, line);
    if (line.empty() || line[0] == char('%'))
      continue;
    istringstream ios(line);
    if (n == 0) {
      ios >> n >> m >> nmz;
      irow.resize(nmz); fill(irow.begin(), irow.end(), size_type(-1));
      jcol.resize(nmz); fill(jcol.begin(), jcol.end(), size_type(-1));
      aval.resize(nmz); fill(aval.begin(), aval.end(), value_type(0));
    } else {
      ios >> irow[k] >> jcol[k] >> aval[k];
      if (ios.fail()) {
        cerr << "Error at " << k << ": " << line << endl;
        abort();
      }
      irow[k]--;
      jcol[k]--;
      k++;
    }
  }

  __n = n;
  __nmz = nmz;
  vector<list<size_type> > ij(__n);
  for (size_type i = 0; i < nmz; i ++)
    ij[irow[i]].push_back(jcol[i]);

  for (size_type i = 0; i < __n; i ++)
    ij[i].sort();

  __hdr.resize(__n + 1);
  __jcol.resize(__nmz);
  __a.resize(__nmz); fill(__a.begin(), __a.end(), value_type(0));
  size_type ii = 0;
  for (size_type i = 0; i < __n; i ++) {
    list<size_type>::iterator k, e = ij[i].end();
    __hdr[i] = ii;
    for (k = ij[i].begin(); k != e; ++ k)
      __jcol[ii ++] = *k;
  }
  __hdr[__n] = ii;

  for (size_type i = 0; i < nmz; i ++)
    A(irow[i], jcol[i]) = aval[i];

  __x.resize(__n); fill(__x.begin(), __x.end(), value_type(0));
  __b.resize(__n); fill(__b.begin(), __b.end(), value_type(0));

  __block.resize(__n);
  fill(__block.begin(), __block.end(), 1);
  __btop.resize(__n);
  for (size_type i = 0; i < __n; i ++)
    __btop[i] = i;
}

void
Matrix::__setup(const Mesh1D &mesh)
{
  __btop.resize(__block.size());

  __n = 0;
  for (size_t i = 0; i < __block.size(); i ++) {
    __btop[i] = __n;
    __n += __block[i];
  }

  vector<list<size_type> > ij(__n);
  for (size_t I = 0; I < __block.size(); I ++)
    for (size_type i = 0; i < __block[I]; i ++)
      for (size_type j = 0; j < __block[I]; j ++)
        ij [__btop[I] + i].push_back(__btop[I]+j);

  for (size_type iL = 0; iL < mesh.nL(); iL ++) {
    const size_type I = mesh.iLN(iL, 0), J = mesh.iLN(iL, 1);
    for (size_type i = 0; i < __block[I]; i ++)
      for (size_type j = 0; j < __block[J]; j ++) {
        ij[__btop[I]+i].push_back(__btop[J]+j);
        ij[__btop[J]+j].push_back(__btop[I]+i);
      }
  }

  __nmz = 0;
  for (size_type i = 0; i < __n; i ++) {
    ij [i].sort();

#if 0
    cout << "i: " << i << ": ";
    list<size_type>::iterator k, e = ij[i].end();
    for (k = ij[i].begin(); k != e; ++ k)
      cout << " " << *k;
    cout << endl;
#endif
    __nmz += ij[i].size();
  }

  __hdr.resize(__n + 1);
  __jcol.resize(__nmz);
  __a.resize(__nmz); fill(__a.begin(), __a.end(), value_type(0));
  size_type ii = 0;
  for (size_type i = 0; i < __n; i ++) {
    list<size_type>::iterator k, e = ij[i].end();
    __hdr[i] = ii;
    for (k = ij[i].begin(); k != e; ++ k)
      __jcol[ii++] = *k;
  }
  __hdr[__n] = ii;
  __x.resize(__n); fill(__x.begin(), __x.end(), value_type(0));
  __b.resize(__n); fill(__b.begin(), __b.end(), value_type(0));
}

int
Matrix::uranus()
{
  size_type j, ip = __n + 1;
  for (size_type i = 0; i < __n; i ++) {  // 行の検査
    __lpt[i] = ip;

    if (__hdr[i] == __hdr[i + 1])  // A の i 行目に要素が無い
      continue;

    if ((j = __jcol[__hdr[i]]) >= i)
      continue;

    while (j < i)  // L(i,j) の検査 ... j < i
      __lpt[ip ++] = j ++;
  }

  __lpt[__n] = ip;
  return ip;
}

int Matrix::cronos()
{
  const value_type eps = 1e-50;

  vector<size_type> list(__n);
  for (size_type i = 0; i < __n; i ++) {  // work 領域の初期化
    list[i] = (__lpt[i+1] == __lpt[i]) ? -1 : __lpt[i];
    // templ[i] = 0.0;
  }

  vector<size_type> list2(__n);
  fill(list2.begin(), list2.end(), -1);

  vector<value_type> tmpl(__n), tmpu(__n);
  fill(tmpl.begin(), tmpl.end(), 0.0);
  fill(tmpu.begin(), tmpu.end(), 0.0);

  // L と U に A(i,j) の値を代入。
  for (size_type i = 0; i < __n; i ++) {  // i行目の処理のループ
    const size_type hI  = __hdr[i];
    const size_type hI1 = __hdr[i + 1];
    for (size_type k = hI; k < hI1; k ++) {  // A(i,*)のループ
      const size_type jj = __jcol[k];  // jj列目の処理
      if (jj < i) {
        tmpl[jj] = __a[k];
        list2[jj] = i;

      } else if (jj > i) {
        size_type kk = list[jj];
        if ((kk < 0)||(__lpt[kk] > i))
          continue;
        const size_type lpt_jj_1 = __lpt[jj + 1];
        while (__lpt[kk] < i) {
          __uval[kk] = 0.0;
          kk ++;
          if (kk == lpt_jj_1) {
            list[jj] = -1;
            goto next;
          }
        }
        __uval[kk ++] = __a[k];
        if (kk == lpt_jj_1)
          list[jj] = -1;
        else
          list[jj] = kk;

      } else {  // if (jj == i)
        __lval [i] = __a[k];

        size_type kk = list [jj];
        if (kk >= 0) {
          while (kk < __lpt[jj + 1])
            __uval[kk ++] = 0.0;
        }
      }
   next:;
    }

    // U の対角要素にはコンストラクタ時に 1.0 が入っている
    // uval[i] = 1.0;

    for (size_type k = __lpt[i]; k < __lpt[i + 1]; k ++) {
      const size_type jj = __lpt[k];
      __lval[k] = ((list2[jj] == i) ? tmpl[jj] : 0.0);
      // lval[k] = tmpl[lpt[k]];
    }

#if 0
    if (i == nprev)
      // 最後は tmpl を元に (0.0 に）戻す必要なし。
      break;
    for (k ~ hI; k < hI1; k ++) {  // 元にもどす。0.0にしておく。
      const size_type jj = jcol[k];
      if (jj < i)
        tmpl [jj] = 0.0;
    }
#endif
  }

  fill(list.begin(), list.end(), -1);

  // L, U の計算
  for (size_type i = 1; i < __n; i ++) {  // 1かあでいい。0は不要
    size_type ip = __lpt[i];
    const size_type np = __lpt[i + 1];

    value_type val;
    if (ip < np) {
      val = __lval[i];

      const size_type j = __lpt[ip];
      list[j] = i;
      value_type vv = __lval[j];
      value_type sl = __lval[ip];
      value_type su = __uval[ip];
      val -= sl * (su / vv);
      tmpu[j] = __uval[ip] = su / vv;
      tmpl[j] = sl;
    } else
      continue;

    for (ip ++; ip < np; ip ++) {
      const size_type j = __lpt[ip];
      list[j] = i;

      value_type sl = __lval[ip];
      value_type su = __uval[ip];
      size_type jp, njp = __lpt[j + 1];
      for (jp = __lpt[j]; jp < njp; jp ++) {
        const size_type k = __lpt[jp];
        if (list[k] == i) {
          sl -= __uval[jp] * tmpl[k];
          su -= __lval[jp] * tmpu[k];
        }
      }
      value_type vv = __lval[j];
      val -= sl * (su / vv);
      __uval[ip] = tmpu[j] = su / vv;
      __lval[ip] = tmpl[j] = sl;
    }

    __lval[i] = val;
    if (std::abs(val) < eps) {
      cerr << "Warning: val=" << val << endl;
      return -1;
    }
  }
  return 0;
}

static void
uvb(vector<Matrix::value_type> &x,
    const vector<Matrix::size_type> &ijm,
    const vector<Matrix::value_type> &val,
    const vector<Matrix::value_type> &b)
{
  const Matrix::size_type n = x.size();
  for (Matrix::size_type i = 0; i < n; i ++) {
    Matrix::value_type r = b[i];
    for (Matrix::size_type k = ijm[i]; k < ijm[i + 1]; k ++)
      r -= val[k] * x[ijm[k]];
    if (std::abs(val[i]) < std::numeric_limits<double>::min()) {
      cerr << "*** CATION: val[" << i << "]=" << val[i] << endl;
      x[i] = r / std::numeric_limits<double>::min();
    } else
      x[i] = r / val[i];
  }
}

static void
uxv(vector<Matrix::value_type> &x,
    const vector<Matrix::size_type> &ijm,
    const vector<Matrix::value_type> &val)
{
  const Matrix::size_type n = x.size();
  for (Matrix::size_type i = n - 1; i >= 0; i --) {
    const Matrix::value_type xx = x[i];
    for (Matrix::size_type k = ijm[i]; k < ijm[i + 1]; k ++)
      x[ijm[k]] -= val[k] * xx;
  }
}

void
Matrix::solve(bool display)
{
  if (display) {
    ofstream ofs("Ab.mtx");
    ofs.precision(17);
    ofs.setf(ios::scientific);
    ofs << "### --- A ---" << endl;
    for (size_type i = 0; i < __n; i ++)
      for (size_type ii = __hdr[i]; ii < __hdr[i + 1]; ii ++)
        ofs << i << " " << __jcol[ii] << " " << __a[ii] << endl;

    ofs << endl << "### --- b ---" << endl;
    for (size_type i = 0; i < __n; i ++)
      ofs << i << " " << __b[i] << endl;
  }

  vector<value_type> t(__n);
  fill(t.begin(), t.end(), value_type(1));
  for (size_type i = 0; i < __n; i ++)
    for(size_type ii = __hdr[i]; ii < __hdr[i + 1]; ii ++) {
      if (i == __jcol[ii])
        if ((t [i] = __a[ii]) == value_type(0))
          t[i] = value_type(1);
    }
  for (size_type i = 0; i < __n; i ++)
    for (size_type ii = __hdr[i]; ii < __hdr[i + 1]; ii ++)
      __a[ii] /= t[__jcol[ii]];

  __lpt.resize(__nmz + 1);
  __lval.resize(__nmz + 1);
  __uval.resize(__nmz + 1);

  uranus();
  cronos();
  uvb(__x, __lpt, __lval, __b);
  uxv(__x, __lpt, __uval);

  for (size_type i = 0; i < __n; i ++)
    for (size_type ii = __hdr[i]; ii < __hdr[i + 1]; ii ++)
      __a[ii] *= t[__jcol[ii]];
  for (size_type i = 0; i < __n; i ++)
    __x[i] /= t[i];

  if (display) {
    ofstream ofs("x.mtx");
    ofs.precision(17);
    ofs.setf(ios::scientific);
    ofs << "### --- x, b-Ax, (b-Ax)/max(b,Ax) ---" << endl;
    for (size_type i = 0; i < __n; i ++) {
      value_type r = __b[i];
      value_type v = abs(__b[i]);
      for (size_type ii = __hdr[i]; ii < __hdr[i + 1]; ii ++) {
        value_type w = __a[ii] * __x[__jcol[ii]];
        r -= w;
        if (v < abs (w))
          v = abs(w);
      }
      if (v == value_type(0))
        v = value_type(1);
      ofs << i << " " << __x[i] << " " << r << " "
          << abs(r / v) << endl;
    }
  }
}
