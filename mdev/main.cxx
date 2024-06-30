//
// Copyright (C) 2024 YYNET.
// This file is part of mdev.
//
// p.25-
#include "ValueType.h"
#include "MaterialInfo.h"
#include "Mesh1D.h"
#include "Field.h"
#include "Newton0carr.h"
#include "Newton2carr.h"

#include <iostream>
#include <vector>
#include <map>
#include <cmath>
#include <cassert>
#include <sstream>
using namespace std;

class MaterialInfo_Si: public MaterialInfo {
 public:
  int priority () const { return 0; }
  bool isSemiConductor () const { return true; }

  value_type eps () const { return 11.7L * PhysConstant::eps0; }
  value_type elec_mu0 () const { return 1417.0; }
  value_type hole_mu0 () const { return 470.5; }

  value_type elecAffinity () const { return 4.17; }
  value_type bandGapEnergy (value_type temp) const { return 1.08; }
  value_type bandGapNarrowing (const value_type &donor,
                               const value_type &acceptor) const {
    const value_type N0 = 1e17;
    const value_type V1 = 9e-3;
    const value_type C = 0.5;
    const value_type N = donor + acceptor;
    if (N <= 0.0)
      return 0.0;
    const value_type N_N0 = N / N0;
    const value_type lnNN0 =
      (N_N0 == 0) ? (log(N) - log(N0)) : log(N_N0);
    assert(!isinf(lnNN0) && !isnan(lnNN0));

    // BGN_SLOTBOOM
    value_type val;
    if (lnNN0 >= 0)
      val = V1 * (lnNN0 + sqrt(lnNN0 * lnNN0 + C));
    else
      val = V1 * C / (sqrt(lnNN0 * lnNN0 + C) - lnNN0);
    return val;
  }

  value_type carrConc (const value_type &temp,
                       const value_type &dEg = 0.0) const {
    return sqrt(effectDensStateValence(temp) * effectDensStateConduction(temp))
      * exp((dEg - bandGapEnergy(temp)) * 0.5 / (PhysConstant::ke * temp));
  }

  value_type builtInPotential (const value_type &temp,
                               const value_type &donor,
                               const value_type &acceptor) const {
    const value_type eT = PhysConstant::ke * temp;
    const value_type cc = donor - acceptor;
    const value_type dEg = bandGapNarrowing(donor, acceptor);
    const value_type ni = carrConc(temp, dEg);
    return eT * ::asinh(cc * 0.5L / ni);
  }
};

class MaterialInfo_SiO2: public MaterialInfo {
public:
  int priority () const { return 100; }
  bool isSemiConductor () const { return false; }

  value_type eps () const { return 3.9L * PhysConstant::eps0; }
  value_type elecAffinity () const { return 0.97; }
  value_type bandGapEnergy (const value_type &temp) const { return 9.0; }
};

#define TOX (100.0e-4)
int main(int argc, char *argv[])
{
  cout.precision(17);
  cout.setf(ios::scientific);

  const value_type T = 300.0;  // [T]

  // const value_type Nd = exp(log(1.0e20));
  // const value_type Na = exp(log(1.0e18));
  const value_type Nd = 1.0e20L;
  const value_type Na = 1.0e18L;

  vector<Recipe> devicerecipes(3);
  devicerecipes[0] = Recipe("Si", 0.5, 100, Nd, 0.0);
  devicerecipes[1] = Recipe("Si", 0.5, 100, 0.0, Na);
  devicerecipes[2] = Recipe("Si", 0.5, 100, Nd, 0.0);

  map<string, const MaterialInfo *> mmap;
  mmap["Si"] = new MaterialInfo_Si;
  mmap["SiO2"] = new MaterialInfo_SiO2;

  vector<const MaterialInfo *> minfo(devicerecipes.size());
  for (size_t i = 0; i < devicerecipes.size(); i ++)
    minfo[i] = mmap[devicerecipes[i].material];

  Mesh1D mesh(devicerecipes, minfo, value_type(0));
  Field field(T, devicerecipes, mesh, minfo);
  {
    field.output("Nd", "Nd_00");
    field.output("Na", "Na_00");
  }

  const value_type DEL_crit = 1.0e-2, RES_crit = 1.0e-5;

  cout << endl
       << "0 carr" << endl;
  Newton0carr n0(T, mesh, minfo, field, DEL_crit, RES_crit);
  n0.setVolt(0.0);
  n0.setup();
  int itr = 0;
  do {
    cout << endl << " #" << ++ itr << " ===" << endl;
    n0.solve();
    n0.update();
    n0.setup();
  } while (! n0.isConverge());

  {
    field.output("psi",  "psi_00");
    field.output("elec", "elec_00");
    field.output("hole", "hole_00");
  }

  cout << endl << "2 carr" << endl;
  Newton2carr n2(T, mesh, minfo, field, DEL_crit, RES_crit);
  const value_type dV = 0.1;
  for (int i = 0; i < 101; i ++) {
    n2.setVolt(i * dV);
    n2.setup();
    itr = 0;
    do {
      cout << endl << " #" << ++itr << " ===" << endl;
      n2.solve();
      n2.update();
      n2.setup();

      ostringstream ostr;
      ostr << i << "_" << itr;
      field.output ("psi",  string("psi_")+ostr.str());
      field.output ("elec", string("elec_")+ostr.str());
      field.output ("hole", string("hole_")+ostr.str());
    } while (! n2.isConverge());

    ostringstream ostr;
    ostr << i;
    field.output ("psi",  string("psi_")+ostr.str());
    field.output ("elec", string("elec_")+ostr.str());
    field.output ("hole", string("hole_")+ostr.str());
  }

  map<string,const MaterialInfo*>::iterator i, e = mmap.end();
  for (i = mmap.begin(); i != e; i ++)
    delete i->second;

  cout << "done." << endl;
  return 0;
}
