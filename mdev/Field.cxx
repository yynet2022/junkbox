//
// Copyright (C) 2024 YYNET.
// This file is part of mdev.
//
#include "Field.h"
#include "Mesh1D.h"
#include "MaterialInfo.h"

#include <iostream>
#include <fstream>
#include <vector>
#include <set>
#include <cmath>
#include <cassert>
using namespace std;

Field::Field (value_type temp,
              const vector<Recipe> &devicerecipes,
              const Mesh1D &mesh,
              const vector<const MaterialInfo *> &minfo)
{
  const size_type nN = mesh.nN();
  __f["ni"].resize(nN);
  __f["psi"].resize(nN);
  __f["Nd"].resize(nN);
  __f["Na"].resize(nN);
  __f["elec"].resize(nN);
  __f["hole"].resize(nN);
  __f["phiN"].resize(nN);
  __f["phiP"].resize(nN);

  vector<value_type> &f_ni   = __f["ni"];
  vector<value_type> &f_psi  = __f["psi"];
  vector<value_type> &f_Nd   = __f["Nd"];
  vector<value_type> &f_Na   = __f["Na"];
  vector<value_type> &f_elec = __f["elec"];
  vector<value_type> &f_hole = __f["hole"];
  vector<value_type> &f_phiN = __f["phiN"];
  vector<value_type> &f_phiP = __f["phiP"];

  fill(f_Nd.begin(), f_Nd.end(), 0.0L);
  fill(f_Na.begin(), f_Na.end(), 0.0L);

  vector<set<int> > sRN(devicerecipes.size());
  for (size_type iN = 0; iN < nN; iN ++) {
    for (int i = 0; i < mesh.nNL(iN); i ++) {
      const size_type iL = mesh.iNL(iN, i);
      const size_type iR = mesh.iLR(iL);
      sRN[iR].insert(iN);
    }
  }
  for (size_t iR = 0; iR < sRN.size(); iR ++) {
    const value_type donor = devicerecipes[iR].donor;
    const value_type acceptor = devicerecipes[iR].acceptor;
    set<int>::iterator i, e = sRN[iR].end();
    for (i = sRN[iR].begin(); i != e; i ++) {
      f_Nd[*i] += donor;
      f_Na[*i] += acceptor;
    }
  }

  const value_type q_kT = PhysConstant::kei / temp;  // q/kT
  for (size_type iN = 0; iN < nN; iN ++) {
    const MaterialInfo *m = 0;
    int priority = 0x0fffffff;  // iR = -1;
    for (int i = 0; i < mesh.nNL(iN); i ++) {
      const size_type iL = mesh.iNL(iN, i);
      const size_type iLR = mesh.iLR(iL);
      const MaterialInfo *mm = minfo[iLR];
      const int p = mm->priority();
      if (p < priority) {
        priority = p;
        // iR = iLR;
        m = mm;
      }
    }
    assert(m != 0);

    const value_type donor = f_Nd[iN];
    const value_type acceptor = f_Na[iN];

    const value_type psi = m->builtInPotential(temp, donor, acceptor);
    const value_type factor = exp(q_kT * psi);
    const value_type dEg = m->bandGapNarrowing(donor, acceptor);
    const value_type ni = m->carrConc(temp, dEg);
    const value_type elec = ni * factor;
    const value_type hole = ni / factor;

    f_ni[iN] = ni;
    f_psi[iN] = psi;
    f_elec[iN] = elec;
    f_hole[iN] = hole;
  }

  fill(f_phiN.begin(), f_phiN.end(), 0.0L);
  fill(f_phiP.begin(), f_phiP.end(), 0.0L);
}

void Field::output (const string &name, const string &fname) const
{
  ofstream ofs(fname.empty() ? name.c_str() : fname.c_str());
  ofs.precision(17);
  ofs.setf(ios::scientific);

  ofs << "### " << name << endl;
  const vector<value_type> &v = __f.at(name);
  for (size_t i = 0; i < v.size(); i ++) {
    ofs << i << " " << v[i] << endl;
  }
}
