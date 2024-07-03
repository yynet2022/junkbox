//
// Copyright (C) 2024 YYNET.
// This file is part of mdev.
//
// p.15-
#include "Newton2carr.h"
#include "Field.h"
#include "Mesh1D.h"
#include "MaterialInfo.h"
#include "Bernoulli.h"
#include <iostream>
#include <fstream>
#include <cmath>
#include <iomanip>
#include <limits>
using namespace std;

Newton2carr::Newton2carr (const value_type &temp,
                          const Mesh1D &mesh,
                          const std::vector<const MaterialInfo *> &minfo,
                          Field &field,
                          const value_type &DEL_crit,
                          const value_type &RES_crit)
    : __T(temp), __mesh(mesh), __minfo(minfo), __mat(0), __field(field),
      __DEL_crit(DEL_crit), __RES_crit(RES_crit),
      __DEL_conv(false), __RES_conv(false)
{
  __block.resize(mesh.nN());
  fill(__block.begin(), __block.end(), 1);
  for (int iN = 0; iN < __mesh.nN(); iN ++)
    if (__minfo[__mesh.iNR(iN)]->isSemiConductor())
      __block[iN] = 3;
  __mat = new Matrix(mesh, __block);
  __Axj.resize(__mesh.nN() * 3);
}

void
Newton2carr::setVolt(const value_type &volt)
{
  cout << endl << "### Volt: " << volt << endl;

  Field::field_type &f_psi  = __field("psi");
  // Field::field_type &f_elec = __field("elec");
  // Field::field_type &f_hole = __field("hole");
  Field::field_type &f_Nd   = __field("Nd");
  Field::field_type &f_Na   = __field("Na");
  // Field::field_type &f_ni   = __field("ni");
  // Field::field_type &f_phiN = __field("phiN");
  // Field::field_type &f_phiP = __field("phiP");

  // Dirichlet Boundary [1]
  // const value_type q_kT = PhysConstant::kei / __T;
  {
    const int iN = 0;
    // const value_type wf = value_type(4.1);
    // f_psi[iN] = volt - wf + __minfo[__mesh.iNR[iN]]->workFunction(__T);

    // const value_type ni = f_ni[iN];

    // const value_type phiP = log(f_hole[iN] / ni) / q_kT + f_psi[iN];
    // const value_type phiN = f_psi[iN] - log(f_elec[iN] / ni) / q_kT;

    const value_type Nd = f_Nd[iN];
    const value_type Na = f_Na[iN];
    f_psi[iN] = volt + __minfo[__mesh.iNR(iN)]->builtInPotential(__T, Nd, Na);

    // const value_type psi = f_psi[iN];
    // const value_type phiP = f_phiP[iN];
    // const value_type phiN = f_phiN[iN];

    // f_hole[iN] = ni * exp((phiP - psi) * q_kT);
    // f_elec[iN] = ni * exp((psi - phiN) * q_kT);
  }
  {
    const int iN = __mesh.nN() - 1;

    // const value_type ni = f_ni[iN];

    // const value_type phiP = log(f_hole[iN] / ni) / q_kT + f_psi[iN];
    // const value_type phiN = f_psi[iN] - log(f_elec[iN] / ni) / q_kT;

    const value_type Nd = f_Nd[iN];
    const value_type Na = f_Na[iN];
    const value_type volt0 = value_type(0);
    f_psi[iN] = volt0 + __minfo[__mesh.iNR(iN)]->builtInPotential(__T, Nd, Na);

    // const value_type psi = f_psi[iN];
    // const value_type phiP = f_phiP[iN];
    // const value_type phiN = f_phiN[iN];

    // f_hole[iN] = ni * exp((phiP - psi) * q_kT);
    // f_elec[iN] = ni * exp((psi - phiN) * q_kT);
  }
}

static const value_type diag = value_type(1e-12);

inline
value_type max3(const value_type &a,
                const value_type &b,
                const value_type &c)
{
  return max(max(abs(a), abs(b)), abs(c));
}

inline
value_type max5(const value_type &a,
                const value_type &b,
                const value_type &c,
                const value_type &d,
                const value_type &e)
{
  return max(max(abs(a), abs(b)), max3(c, d, e));
}

void
Newton2carr::setup()
{
  Field::field_type &f_ni   = __field("ni");
  Field::field_type &f_psi  = __field("psi");
  Field::field_type &f_elec = __field("elec");
  Field::field_type &f_hole = __field("hole");
  Field::field_type &f_Nd   = __field("Nd");
  Field::field_type &f_Na   = __field("Na");

  // const value_type q_kT = PhysConstant::kei / __T;
  // const value_type q2_kT = PhysConstant::q / (PhysConstant::ke * __T);

  __mat->clear();
  fill(__Axj.begin(), __Axj.end(), value_type(0));

  vector<value_type> rpmax(__mesh.nN());
  fill(rpmax.begin(), rpmax.end(), value_type(0));

  vector<value_type> remax(__mesh.nN());
  fill(remax.begin(), remax.end(), value_type(0));

  vector<value_type> rhmax(__mesh.nN());
  fill(rhmax.begin(), rhmax.end(), value_type(0));

  for (int iL = 0; iL < __mesh.nL(); iL ++) {
    const MaterialInfo *ml = __minfo[__mesh.iLR(iL)];

    const value_type eps = ml->eps();
    const value_type Fij = __mesh.vF(iL);
    const value_type len = __mesh.vL(iL);
    const int i = __mesh.iLN(iL, 0);
    const int j = __mesh.iLN(iL, 1);

    __mat->A(i, i, 0, 0) +=  eps * Fij / len;
    __mat->A(i, j, 0, 0) += -eps * Fij / len;

    __mat->A(j, j, 0, 0) +=  eps * Fij / len;
    __mat->A(j, i, 0, 0) += -eps * Fij / len;

    value_type psi_i = f_psi[i];
    value_type psi_j = f_psi[j];

    const MaterialInfo *mi = __minfo[__mesh.iNR(i)];
    const MaterialInfo *mj = __minfo[__mesh.iNR(j)];
    if (ml != mi)
      psi_i += -mi->workFunction(__T) + ml->workFunction(__T);
    if (ml != mj)
      psi_j += -mj->workFunction(__T) + ml->workFunction(__T);
    const value_type dPsi = psi_j - psi_i;

    const value_type val = -eps * dPsi * Fij / len;
    __mat->b(i) -=  val; // = -eps *  dPsi * Fij / len
    __mat->b(j) -= -val; // = -eps * -dPsi * Fij / len

    rpmax[i] = max3(rpmax[i],
                    abs(eps * psi_i * Fij / len),
                    abs(eps * psi_j * Fij / len));
    rpmax[j] = max3(rpmax[j],
                    abs(eps * psi_i * Fij / len),
                    abs(eps * psi_j * Fij / len));

    __Axj[i*3] = std::max(__Axj[i*3], std::abs(-eps * Fij / len * psi_j));
    __Axj[j*3] = std::max(__Axj[j*3], std::abs(-eps * Fij / len * psi_i));

    if (! ml->isSemiConductor())
      continue;

    const value_type kT_l = PhysConstant::k * __T / len;
    const value_type q_kT = PhysConstant::kei / __T;

    const value_type ni_i = f_ni[i];
    const value_type ni_j = f_ni[j];
    const value_type dEb = log(ni_j / ni_i);

    const value_type delta_n = q_kT *  dPsi + dEb;
    const value_type delta_p = q_kT * -dPsi + dEb;
    const value_type Bn   = Bernoulli::B(-delta_n);
    const value_type Bn_j = Bernoulli::B( delta_n);

    const value_type Bp   = Bernoulli::B(-delta_p);
    const value_type Bp_j = Bernoulli::B( delta_p);

    const value_type n_i = f_elec[i];
    const value_type n_j = f_elec[j];

    const value_type p_i = f_hole[i];
    const value_type p_j = f_hole[j];

    const value_type yn = -delta_n + log(n_j / n_i);
    const value_type yp = -delta_p + log(p_j / p_i);
    const value_type Qn = n_i * Bernoulli::UD(yn);
    const value_type Qp = p_i * Bernoulli::UD(yp);

    const value_type qnE =  kT_l * (Bn * Qn);
    const value_type qpE = -kT_l * (Bp * Qp);

    const value_type dBndx = Bernoulli::BdB(-delta_n);
    const value_type dBpdx = Bernoulli::BdB(-delta_p);

    const value_type dBndPi = dBndx * q_kT;
    const value_type dBndPj = -dBndPi;
    const value_type dBndni = value_type(0);
    const value_type dBndnj = value_type(0);

    const value_type dBpdPi = -dBpdx * q_kT;
    const value_type dBpdPj = -dBpdPi;
    const value_type dBpdpi = value_type(0);
    const value_type dBpdpj = value_type(0);

    const value_type dQndPi = n_i * exp(yn) * q_kT;
    const value_type dQndPj = -dQndPi;
    const value_type dQndni = -value_type(1);
    const value_type dQndnj = n_i * exp(yn) / n_j;

    const value_type dQpdPi = -p_i * exp(yp) * q_kT;
    const value_type dQpdPj = -dQpdPi;
    const value_type dQpdpi = -value_type(1);
    const value_type dQpdpj = p_i * exp(yp) / p_j;

    const value_type dqnE_dPsi_i  = (dBndPi * Qn + Bn * dQndPi) * kT_l;
    const value_type dqnE_dElec_i = (dBndni * Qn + Bn * dQndni) * kT_l;
    const value_type dqnE_dPsi_j  = (dBndPj * Qn + Bn * dQndPj) * kT_l;
    const value_type dqnE_dElec_j = (dBndnj * Qn + Bn * dQndnj) * kT_l;

    const value_type dqpE_dPsi_i  = -(dBpdPi * Qp + Bp * dQpdPi) * kT_l;
    const value_type dqpE_dHole_i = -(dBpdpi * Qp + Bp * dQpdpi) * kT_l;
    const value_type dqpE_dPsi_j  = -(dBpdPj * Qp + Bp * dQpdPj) * kT_l;
    const value_type dqpE_dHole_j = -(dBpdpj * Qp + Bp * dQpdpj) * kT_l;

    const value_type emu = ml->elec_mu0();
    const value_type hmu = ml->hole_mu0();

    // ---
    __mat->A(i, i, 1, 0) += dqnE_dPsi_i  * emu * Fij;
    __mat->A(i, i, 1, 1) += dqnE_dElec_i * emu * Fij;
    __mat->A(i, i, 1, 2) += value_type(0);

    __mat->A(i, j, 1, 0) += dqnE_dPsi_j  * emu * Fij;
    __mat->A(i, j, 1, 1) += dqnE_dElec_j * emu * Fij;
    __mat->A(i, j, 1, 2) += value_type(0);

    __mat->A(j, j, 1, 0) += -dqnE_dPsi_j  * emu * Fij;
    __mat->A(j, j, 1, 1) += -dqnE_dElec_j * emu * Fij;
    __mat->A(j, j, 1, 2) += value_type(0);

    __mat->A(j, i, 1, 0) += -dqnE_dPsi_i  * emu * Fij;
    __mat->A(j, i, 1, 1) += -dqnE_dElec_i * emu * Fij;
    __mat->A(j, i, 1, 2) += value_type(0);

    __mat->b(i, 1) -=  qnE * emu * Fij;
    __mat->b(j, 1) -= -qnE * emu * Fij;

    remax[i] = max3(remax[i],
                    emu * kT_l * Bn_j * n_j * Fij,
                    emu * kT_l * Bn   * n_i * Fij);
    remax[j] = max3(remax[j],
                    emu * kT_l * Bn_j * n_j * Fij,
                    emu * kT_l * Bn   * n_i * Fij);
    __Axj[i*3+1] = std::max(__Axj[i*3+1],
                            std::abs(dqnE_dElec_j * emu * Fij * n_j));
    __Axj[j*3+1] = std::max(__Axj[j*3+1],
                            std::abs(dqnE_dElec_i * emu * Fij * n_i));

    // ---
    __mat->A(i, i, 2, 0) += -dqpE_dPsi_i  * hmu * Fij;
    __mat->A(i, i, 2, 1) += value_type(0);
    __mat->A(i, i, 2, 2) += -dqpE_dHole_i * hmu * Fij;

    __mat->A(i, j, 2, 0) += -dqpE_dPsi_j  * hmu * Fij;
    __mat->A(i, j, 2, 1) += value_type(0);
    __mat->A(i, j, 2, 2) += -dqpE_dHole_j * hmu * Fij;

    __mat->A(j, j, 2, 0) += dqpE_dPsi_j  * hmu * Fij;
    __mat->A(j, j, 2, 1) += value_type(0);
    __mat->A(j, j, 2, 2) += dqpE_dHole_j * hmu * Fij;

    __mat->A(j, i, 2, 0) += dqpE_dPsi_i  * hmu * Fij;
    __mat->A(j, i, 2, 1) += value_type(0);
    __mat->A(j, i, 2, 2) += dqpE_dHole_i * hmu * Fij;

    __mat->b(i, 2) -= -qpE * hmu * Fij;
    __mat->b(j, 2) -=  qpE * hmu * Fij;

    rhmax[i] = max3(rhmax[i],
                    emu * kT_l * Bp_j * p_j * Fij,
                    emu * kT_l * Bp   * p_i * Fij);
    rhmax[j] = max3(rhmax[j],
                    emu * kT_l * Bp_j * p_j * Fij,
                    emu * kT_l * Bp   * p_i * Fij);
    __Axj[i*3+2] = std::max(__Axj[i*3+2],
                            std::abs(dqpE_dHole_j * hmu * Fij * p_j));
    __Axj[j*3+2] = std::max(__Axj[j*3+2],
                            std::abs(dqpE_dHole_i * hmu * Fij * p_i));
  }

  for (int iN = 0; iN < __mesh.nN(); iN ++) {
    const value_type Nd   = f_Nd[iN];
    const value_type Na   = f_Na[iN];
    const value_type elec = f_elec[iN];
    const value_type hole = f_hole[iN];
    value_type cvN  = value_type(0);

    for (int i = 0; i < __mesh.nNL(iN); i ++) {
      const int iL = __mesh.iNL(iN, i);
      if (__minfo[__mesh.iLR(iL)]->isSemiConductor()) {
        const value_type cv = __mesh.vCV(iN, i);
        cvN += cv;

        // A(i,i) += dF
        //         = d(-q(Nd - Na + p - n) * cv) / d....
        //         = d( q(n - p) * cv) / d....
        //         = q * q/kT * (n + p) * cv
        // __mat->A(iN, iN, 0, 0) += q2_kT * (elec + hole) * cv;

        //  = d(-q (Nd - Na + p - n) * cv)/dn|dp
        //  =  q * 1 * cv: n
        //  = -q * 1 * cv: p
        __mat->A(iN, iN, 0, 1) +=  PhysConstant::q * cv;
        __mat->A(iN, iN, 0, 2) += -PhysConstant::q * cv;

        // b(i) -= F
        //       = -q(Nd - Na + p - n) * cv
        __mat->b(iN) -= -PhysConstant::q * (Nd - Na + hole - elec) * cv;
      }
    }

    rpmax[iN] = max5(rpmax[iN],
                     PhysConstant::q * Nd * cvN,
                     PhysConstant::q * Na * cvN,
                     PhysConstant::q * hole * cvN,
                     PhysConstant::q * elec * cvN);
  }

  // Dirichlet Boundary [2]
  {
    const int iN = 0;
    const vector<Matrix::size_type> &hdr = __mat->hdr();
    const vector<Matrix::size_type> &jcol = __mat->jcol();
    const vector<Matrix::size_type> &btop = __mat->btop();
    const vector<Matrix::size_type> &block = __mat->block();
    vector<Matrix::value_type> &a = __mat->a();
    for (int j = 0; j < block[iN]; j ++) {
      for (int ii = hdr[btop[iN] + j]; ii < hdr[btop[iN] + j + 1]; ii ++)
        a[ii] = (jcol[ii] == btop[iN] + j) ? diag : value_type(0);
      __mat->b(iN, j) = value_type(0);
    }
  }
  {
    const int iN = __mesh.nN() - 1;
    const vector<Matrix::size_type> &hdr = __mat->hdr();
    const vector<Matrix::size_type> &jcol = __mat->jcol();
    const vector<Matrix::size_type> &btop = __mat->btop();
    const vector<Matrix::size_type> &block = __mat->block();
    vector<Matrix::value_type> &a = __mat->a();
    for (int j = 0; j < block[iN]; j ++) {
      for (int ii = hdr[btop[iN] + j]; ii < hdr[btop[iN] + j + 1]; ii ++)
        a[ii] = (jcol[ii] == btop[iN] + j) ? diag : value_type(0);
      __mat->b(iN, j) = value_type(0);
    }
  }

  {
    cout << "||b|| = " << __mat->b2norm() << endl;

    const value_type cond_minV [] = {1e-3, 1e-3, 1e-3};
    value_type maxR [] = {0, 0, 0};
    size_type idxR[] = {-1, -1, -1};
    value_type maxB[] = {0, 0, 0};
    size_type idxB[] = {-1, -1, -1};
    value_type maxQ[] = {0, 0, 0};
    size_type idxQ[] = {-1, -1, -1};

    for (size_type iN = 0; iN < __mesh.nN(); iN ++) {
      for (int j = 0; j < __block[iN]; j ++) {
        if (abs(maxB[j]) < abs(__mat->b(iN, j))) {
          maxB[j] = __mat->b(iN, j);
          idxB[j] = iN;
        }

        // = b / (maxAxj + std::abs(Aii*cond_minV[j]))
        const value_type r = __Axj[iN*3+j] + abs(__mat->A(iN,iN,j,j)*cond_minV[j]);
        if ((r != 0.0)&&(abs(maxR[j]) < abs(__mat->b(iN,j)/r))) {
          maxR[j] = __mat->b(iN, j) / r;
          idxR[j] = iN;
        }
      }

      const value_type qp = __mat->b(iN, 0) / rpmax[iN];
      if (abs(maxQ[0]) < abs(qp)) {
        maxQ[0] = qp;
        idxQ[0] = iN;
      }

      const value_type qe = __mat->b(iN, 1) / remax[iN];
      if (abs(maxQ[1]) < abs(qe)) {
        maxQ[1] = qe;
        idxQ[1] = iN;
      }

      const value_type qh = __mat->b(iN, 2) / rhmax[iN];
      if (abs(maxQ[2]) < abs(qh)) {
        maxQ[2] = qh;
        idxQ[2] = iN;
      }
    }

    const string name_list[3] = {"psi ", "elec", "hole"};
    int pr = cout.precision();

    cout << "b(max):" << endl;
    for (int j = 0; j < 3; j ++)
      cout << " " << name_list[j] << ": "
           << setw(3) << idxB[j] << ": "
           << __mat->b(idxB[j], j) << endl;

    __RES_conv = true;
    cout << "RES:" << endl;
    for (int j = 0; j < 3; j ++) {
      if (! (abs(maxR[j]) < __RES_crit))
        __RES_conv = false;

      cout << " " << name_list[j] << ": "
           << setw(3) << idxR[j] << ": "
           << setprecision(6) << maxR[j] << setprecision(pr)
           << " (b=" << (idxR[j] >= 0 ? __mat->b(idxR[j],j): 0.0)
           << ")" << endl;
    }

    cout << "newRES: " << endl;
    for (int j = 0; j < 3; j ++) {
      cout << " " << name_list[j] << ": "
           << setw(3) << idxQ[j] << ": "
           << setprecision(6) << maxQ[j] << setprecision(pr)
           << " (b=" << (idxQ[j] >= 0 ? __mat->b(idxQ[j], j): 0)
           << ")" << endl;
    }
  }
}

void
Newton2carr::solve()
{
  __mat->solve(true);

  {
    cout << "||x|| = " << __mat->x2norm() << endl
         << "||r|| = " << __mat->r2norm() << endl;

    const vector<value_type> *f_val[] = {
      &__field("psi"), &__field("elec"), &__field("hole")};

    value_type maxX[] = {0, 0, 0};
    int idxX[] = {0, 0, 0};
    for (int iN = 1; iN < __mesh.nN(); iN ++)
      for (int j = 0; j < __block[iN]; j ++)
        if (abs(maxX[j]) <= abs(__mat->x(iN, j))) {
          maxX[j] = __mat->x(iN, j);
          idxX[j] = iN;
        }

    const string name_list[] = {"psi ", "elec", "hole"};
    cout << "x(max):" << endl;
    for (int j = 0; j < 3; j ++)
      cout << " " << name_list[j] << ": " << setw(3) << idxX[j]
           << ": " << __mat->x(idxX[j], j)
           << " (v=" << (*(f_val[j]))[idxX[j]] << ")" << endl;
  }
}

static void
__output(const string &fname, const vector<value_type> &v)
{
  ofstream ofs(fname.c_str());
  ofs.precision(17);
  ofs.setf(ios::scientific);
  for(size_t i = 0; i < v.size(); i ++)
    ofs << i << " " << v[i] << endl;
}

void
Newton2carr::update()
{
  Field::field_type &f_psi  = __field("psi");
  Field::field_type &f_elec = __field("elec");
  Field::field_type &f_hole = __field("hole");

  // const value_type q_kT = PhysConstant::kei / __T;

  const int n = __mesh.nN();
  value_type dampf = 1.0;
  const value_type fact = 0.5;
  const value_type ulimv = std::numeric_limits<float>::min();
  bool iscont = true;
  while (iscont) {
    iscont = false;
    for (int iN = 0; iN < n; iN ++) {
      if (! __minfo[__mesh.iNR(iN)]->isSemiConductor())
        continue;

      while (f_elec[iN] + dampf * __mat->x(iN, 1) < ulimv) {
        cout << "Warn: elec[" << iN << "]= "
             << f_elec[iN] << " + "  << dampf  * __mat->x(iN, 1)
             << " = " << (f_elec[iN] + dampf * __mat->x(iN, 1)) << endl;
        dampf *= fact;
        iscont = true;
        break;
      }
      while (f_hole[iN] + dampf * __mat->x(iN, 2) < ulimv) {
        cout << "Warn: hole[" << iN << "]= "
             << f_hole[iN] << " + "  << dampf  * __mat->x(iN, 2)
             << " = " << (f_hole[iN] + dampf * __mat->x(iN, 2)) << endl;
        dampf *= fact;
        iscont = true;
        break;
      }
    }
  }
  cout << "Damping factor: " << dampf << endl;
  dampf = 1.0;

  vector<value_type> rd_psi(n), rd_elec(n), rd_hole(n);
  for (int iN = 0; iN < n; iN ++) {
    f_psi[iN] += dampf * __mat->x(iN);
    rd_psi[iN] = abs(__mat->x(iN) / f_psi[iN]);

    if (! __minfo[__mesh.iNR(iN)]->isSemiConductor())
      continue;

    f_elec[iN] += dampf * __mat->x(iN, 1);
    if (f_elec[iN] < ulimv)
      f_elec[iN] = ulimv;
    rd_elec[iN] = abs(__mat->x(iN, 1) / f_elec[iN]);

    f_hole[iN] += dampf * __mat->x(iN, 2);
    if (f_hole[iN] < ulimv)
      f_hole[iN] = ulimv;
    rd_hole[iN] = abs(__mat->x(iN, 2) / f_hole[iN]);
  }

  bool debug = false;
  if (debug) {
    __field.output("psi");
    __field.output("elec");
    __field.output("hole");

    __output("rd_psi", rd_psi);
    __output("rd_elec", rd_elec);
    __output("rd_hole", rd_hole);
  }

  const vector<value_type> *f_val[] = {&f_psi, &f_elec, &f_hole};
  value_type maxV[] = {0, 0, 0};
  for (int iN = 0; iN < __mesh.nN(); iN ++)
    for (int j = 0; j < __block[iN]; j ++) {
      const vector<value_type> &f_v = *(f_val[j]);
      if (abs(maxV[j]) < abs(f_v[iN]))
        maxV[j] = f_v[iN];
    }

  const value_type cond_minV [] = {1e-3, 1e-3, 1e-3};
  value_type cond_maxR[] = {0, 0, 0};
  int cond_idxR[] = {-1, -1, -1};
  value_type cond_maxQ[] = {0, 0, 0};
  int cond_idxQ[] = {-1, -1, -1};
  value_type cond_maxW[] = {0, 0, 0};
  int cond_idxW[] = {-1, -1, -1};

  for (int iN = 0; iN < __mesh.nN(); iN ++)
    for (int j = 0; j < __block[iN]; j ++) {
      const vector<value_type> &f_v = *(f_val[j]);
      const value_type v = __mat->x(iN, j) / (abs(f_v[iN]) + cond_minV[j]);
      if (abs(cond_maxR[j]) <= abs(v)) {
        cond_maxR[j] = v;
        cond_idxR[j] = iN;
      }
      const value_type q = __mat->x(iN, j) / abs(maxV[j]);
      if (abs(cond_maxQ[j]) <= abs(q)) {
        cond_maxQ[j] = q;
        cond_idxQ[j] = iN;
      }
      const value_type w = __mat->x(iN, j) / (abs(f_v[iN]) + 1e-10*abs(maxV[j]));
      if (abs(cond_maxW[j]) <= abs(w)) {
        cond_maxW[j] = w;
        cond_idxW[j] = iN;
      }
    }

  const string name_list[] = {"psi ", "elec", "hole"};
  int pr = cout.precision();
  __DEL_conv = true;
  cout << "DEL:" << endl;
  for (int j = 0; j < 3; j ++) {
    if (! (abs(cond_maxR[j]) < __DEL_crit))
      __DEL_conv = false;

    const vector<value_type> &f_v = *(f_val[j]);
    cout << " " << name_list[j] << ": "
         << setw(3) << cond_idxR[j] << ": "
         << setprecision(6) << cond_maxR[j] << setprecision(pr)
         << " (x=" << __mat->x(cond_idxR[j], j)
         << " v=" << f_v[cond_idxR[j]] << ")" << endl;
  }

  cout << "DEL/max:" << endl;
  for (int j = 0; j < 3; j ++) {
    // const vector<value_type> &f_v = *(f_val[j]);
    cout << " " << name_list[j] << ": "
         << setw(3) << cond_idxQ[j] << ": "
         << setprecision(6) << cond_maxQ[j] << setprecision(pr)
         << " (x=" << __mat->x(cond_idxQ[j], j)
         << " v=" << maxV[j] << ")" << endl;
  }

  cout << "DEL/(x+max):" << endl;
  __DEL_conv = true;
  for (int j = 0; j < 3; j ++) {
    if (! (abs(cond_maxW[j]) < __DEL_crit))
      __DEL_conv = false;

    const vector<value_type> &f_v = *(f_val[j]);
    cout << " " << name_list[j] << ": "
         << setw(3) << cond_idxW[j] << ": "
         << setprecision(6) << cond_maxW[j]
         << " (x=" << __mat->x(cond_idxW[j], j)
         << " v=" << f_v[cond_idxW[j]] << "+"
         << 1e-10*maxV[j] << ")"
         << setprecision(pr) << endl;
  }
}

bool
Newton2carr::isConverge()
{
  cout << "### DEL " << ((__DEL_conv) ? "converge" : "not converge") << endl;
  cout << "### RES " << ((__RES_conv) ? "converge" : "not converge") << endl;
  return __DEL_conv && __RES_conv;
}
